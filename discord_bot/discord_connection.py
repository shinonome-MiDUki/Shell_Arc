import re
import os
import sys
import io
import asyncio

import discord
from discord.ext import commands
from discord import Webhook as Webhook
from dotenv import load_dotenv

proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if proj_root not in sys.path:
    sys.path.append(proj_root)

from backend.request_r2 import Cloudflare_R2_service as R2
from backend.common_initialisation import CommonInitialisation as Common
from backend.file_operation import FileOperation as FileOp
from discord_notice_webhook import DiscordNotice as Notice

load_dotenv(verbose=True)
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)
TOKEN = os.environ.get("Discord_token")
SERVER_ID = os.environ.get("Discord_server_id")
dc_client = discord.Client(intents=discord.Intents.all())

shell_arc_bot = commands.Bot(command_prefix="..", intents=discord.Intents.all())

TOTAL_CUT_COUNT = 5

component_reference_dict = {
    "genga" : "原画",
    "nakawari" : "中割り", 
    "haikei" : "背景",
    "satsuei" : "撮影",
    "hennsyu" : "編集",
    "原画" : "原画",
    "中割り" : "中割り",
    "背景" : "背景",
    "撮影" : "撮影",
    "編集" : "編集",
    "g" : "原画",
    "n" : "中割り",
    "h" : "背景",
    "s" : "撮影",
    "hen" : "編集"
}
component_index_reference_dict = {
    "原画" : 1,
    "中割り" : 2,
    "背景" : 3,
    "撮影" : 4,
    "編集" : 5
}
rev_component_index_reference_dict = {v: k for k, v in component_index_reference_dict.items()}

class SubmissionSelectionView(discord.ui.View): 
    def __init__(self, timeout=120, message=None):
        super().__init__(timeout=timeout)
        self.message = message

    @discord.ui.select(
        cls=discord.ui.Select,
        placeholder="提出する部分を選択してください",
        options=[
            discord.SelectOption(label="原画"),
            discord.SelectOption(label="中割り"),
            discord.SelectOption(label="背景"),
            discord.SelectOption(label="撮影"),
            discord.SelectOption(label="編集"),
        ]
    )
    async def select(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer()

        message = self.message
        channel_name = str(message.channel.name.lower())
        try:
            submitting_cut = str(channel_name.split("_")[0])
            submitting_cut = re.sub(r"[^\d]", "", submitting_cut)
            submitting_cut = int(submitting_cut)
            submitting_person = str(channel_name.split("_")[1])
            submitting_component = str(select.values[0])
        except:
            await message.channel.send("!!ERROR!!")
            return
        print(submitting_cut)
        print(submitting_component)

        if submitting_person != str(message.author.display_name):
            await message.channel.send("Warning : 提出者アカウント名はチャンネルで指定された担当者名と異なります")
            submitting_person = str(message.author.display_name)
        await interaction.channel.send(f"カット{submitting_cut}・{submitting_component} 提出しますか（はい・いいえ）")
        def check(m):
            return m.author == message.author and m.channel == message.channel
        try:
            reply_message = await shell_arc_bot.wait_for('message', check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await message.channel.send("時間超過です。やり直してください")
        except:
            await message.channel.send("!!ERROR!!")
        if reply_message.content == "はい":
            shell_arc_bot.dispatch("push_action", message, submitting_cut, submitting_component, submitting_person)
        else:
            await message.channel.send("提出が棄却されました")

class ReviewSelectionView(discord.ui.View): 
    def __init__(self, timeout=120, message=None):
        super().__init__(timeout=timeout)
        self.message = message

    @discord.ui.select(
        cls=discord.ui.Select,
        placeholder="提出する部分を選択してください",
        options=[
            discord.SelectOption(label="原画"),
            discord.SelectOption(label="中割り"),
            discord.SelectOption(label="背景"),
            discord.SelectOption(label="撮影"),
            discord.SelectOption(label="編集"),
        ]
    )
    async def select(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer()

        message = self.message
        channel_name = str(message.channel.name.lower())
        try:
            reviewing_cut = str(channel_name.split("_")[0])
            reviewing_cut = re.sub(r"[^\d]", "", reviewing_cut)
            reviewing_cut = int(reviewing_cut)
            reviewing_person = str(message.author.display_name)
            reviewing_component = str(select.values[0])
        except:
            await message.channel.send("!!ERROR!!")
            return
        await message.channel.send("許可しますか（はい・いいえ）")
        def check(m):
            return m.author == message.author and m.channel == message.channel
        try:
            reply_message = await shell_arc_bot.wait_for('message', check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await message.channel.send("時間超過です。やり直してください")
        if reply_message.content == "はい":
            shell_arc_bot.dispatch("reviewing_action", message, reviewing_cut, reviewing_component, reviewing_person)
        else:
            await message.channel.send("許可コマンドが棄却されました")
        

@shell_arc_bot.event
async def submit_file(message, submitting_person, submitting_cut, submitting_component, submission_raw):
    common = Common()
    fileop = FileOp()

    #access firebase database
    proj_setting_data = common.proj_setting_data #project setting data dictionary
    ref_collection = common.ref_collection #project main data referncer

    #access spreadsheet
    spreadsheet = common.spreadsheet
    loadGS = common.loadGS

    submitting_person = submitting_person
    submitting_cut = submitting_cut
    submitting_component = submitting_component

    working_data = fileop.work_info(proj_setting_data, submitting_component)
    working_index = working_data["working_index"]
    working_component = working_data["working_component"]
    required_format = working_data["required_format"]
    ref_work_obj = ref_collection.collection(f"cut{submitting_cut:02}").document(working_component)
    ref_work = ref_work_obj.get()
    work_data = ref_work.to_dict()
    
    submission_format_re = re.findall(f".[a-z]+\?", str(submission_raw.url))
    submission_format = submission_format_re[0].lstrip(".").rstrip("?")
    if submission_format not in required_format:
        required_format_str = ""
        for f in required_format:
            required_format_str += f + " "
        await message.channel.send(f"{required_format_str}形式で提出してください")
        return
    else:
        submission_bytes = await submission_raw.read()
        submission = io.BytesIO(submission_bytes)

    current_take = int(work_data["current_take"]) + 1
    renamed = fileop.renamed(proj_setting_data, working_index, submitting_cut, current_take)

    if work_data["temporary"]["naming"] != None:
        temporary = {"naming": renamed, "cut": submitting_cut, "take": current_take, "creator": str(submitting_person), "reviewer": None, "comments": None}
        structure = fileop.update_database(current_take=current_take, work_data=work_data, temporary=temporary, non_active=work_data["temporary"])
    else:
        temporary = {"naming": renamed, "cut": submitting_cut, "take": current_take, "creator": str(submitting_person), "reviewer": None, "comments": None}
        structure = fileop.update_database(current_take=current_take, work_data=work_data, temporary=temporary)
    ref_work_obj.update(structure)

    r2 = R2(common.s3_client)
    r2.upload_file(submission, f"{proj_setting_data['collection_name']}/cut{submitting_cut:02}/{working_component}/{renamed}.{required_format[0]}")

    loadGS.load_spreadsheet(spreadsheet=spreadsheet,
                            cut_index=submitting_cut,
                            target_info="member",
                            update_info=submitting_person,
                            component_index=working_index
                            )
    
    loadGS.load_spreadsheet(spreadsheet=spreadsheet,
                            cut_index=submitting_cut,
                            target_info="situation",
                            update_info="作業中",
                            component_index=working_index)
    
    await message.channel.send(f"カット{submitting_cut}・{submitting_component} にアップロードしました")
    notice = Notice()
    notice.discord_notice(submitting_cut, submitting_component, current_take, submitting_person)

@shell_arc_bot.event
async def approve_file(message, reviewing_person, reviewing_cut, reviewing_component):
    common = Common()
    fileop = FileOp()

    #access firebase database
    ref_setting_obj = common.ref_setting_obj  #project setting data object   
    ref_setting = common.ref_setting #project setting data referncer
    proj_setting_data = common.proj_setting_data #project setting data dictionary
    ref_collection = common.ref_collection #project main data referncer

    #access spreadsheet
    spreadsheet = common.spreadsheet
    loadGS = common.loadGS
    
    #obtain or set needed variables 
    cut_num = int(proj_setting_data["cut_number"])
    component_number = int(proj_setting_data["component_number"])

    reviewing_cut = int(reviewing_cut)
    reviewing_person = str(reviewing_person)
    reviewing_component = reviewing_component
    working_data = fileop.work_info(proj_setting_data, reviewing_component)
    working_index = working_data["working_index"]
    working_component = working_data["working_component"]

    ref_work_obj = ref_collection.collection(f"cut{reviewing_cut:02}").document(working_component)
    ref_work = ref_work_obj.get()
    work_data = ref_work.to_dict()

    if work_data["temporary"]["naming"] == None:
        await message.channel.send("検査待ちの提出物はありません")
        return
    
    if work_data["active"]["naming"] != None:
        structure = fileop.update_database(work_data=work_data, active=work_data["temporary"], temporary="clr", non_active=work_data["active"])
        ref_work_obj.update(structure)
    else:
        structure = fileop.update_database(work_data=work_data, active=work_data["temporary"], temporary="clr")
        ref_work_obj.update(structure)
        
        current_progress = float(proj_setting_data[f"component{working_index}"]["progress"])
        current_progress += (1 / cut_num)
        loadGS.load_progress(spreadsheet, working_index, False, cut_num)
        ref_setting_obj.update({f"component{working_index}.progress" : current_progress})

    loadGS.load_spreadsheet(spreadsheet=spreadsheet, 
                            cut_index=reviewing_cut,
                            target_info="situation",
                            update_info="完了",
                            component_index=working_index
                            )
    await message.channel.send(f"カット{reviewing_cut}・{reviewing_component}は確定されました")


@shell_arc_bot.event
async def on_ready():
    print("ログインしました")

@shell_arc_bot.event
async def on_push_action(message, submitting_cut, submitting_component, submitting_person):
    submitting_component = component_reference_dict[submitting_component]
    submission_raw = message.attachments[0]
    await submit_file(message, submitting_person, submitting_cut, submitting_component, submission_raw)

@shell_arc_bot.event
async def on_reviewing_action(message, reviewing_cut, reviewing_component_raw, reviewing_person):
    reviewing_component = component_reference_dict[reviewing_component_raw]
    await approve_file(message, reviewing_person, reviewing_cut, reviewing_component)

@shell_arc_bot.command()
async def up(ctx):
    message = ctx.message
    if "_" not in message.channel.name:
        return
    if not message.attachments:
        await message.channel.send("ファイルを添付してから提出してくださいccc")
        return
    view = SubmissionSelectionView(timeout=None, message=message)
    await ctx.send(view=view)

@shell_arc_bot.command()
async def appr(ctx):
    message = ctx.message
    if "_" not in message.channel.name:
        return
    view = ReviewSelectionView(timeout=None, message=message)
    await ctx.send(view=view)

@shell_arc_bot.command()
async def ask(ctx):
    message = ctx.message
    if message.channel.name != "担当作業問い合わせ":
        return
    try:
        asking_person = str(message.content.split(" ")[1])
    except:
        asking_person = str(message.author.display_name)
    await message.channel.send("検索中...\n10秒ほどお待ちいただく場合があります")
    common = Common()
    loadGS = common.loadGS
    scheduled_work_list = []
    for cut_num in range(1, TOTAL_CUT_COUNT+1):
        for part_num in range(1, len(component_index_reference_dict)+1):
            person_incharge = str(loadGS.load_spreadsheet(spreadsheet=common.spreadsheet, 
                            cut_index=cut_num, 
                            target_info="member", 
                            update_info=None, 
                            component_index=part_num
                            ))
            if person_incharge == asking_person:
                cut_channel = discord.utils.find(lambda c: c.name.startswith(f"{cut_num}_"), message.guild.text_channels)
                scheduled_work_list.append(f"カット{cut_num} {rev_component_index_reference_dict[part_num]} <#{cut_channel.id}>")
                print(cut_channel)
                print(type(cut_channel))
                try:
                    print(cut_channel.id)
                    print(str(cut_channel))
                except:
                    pass
                
    query_answer_message = f"{asking_person} : "
    if scheduled_work_list:
        for scheduled_work in scheduled_work_list:
            query_answer_message += f"\n{scheduled_work}"
    else:
        query_answer_message += "担当作業がありません"
    await message.channel.send(query_answer_message)

@shell_arc_bot.command()
async def reg(ctx):
    message = ctx.message
    if "_" not in message.channel.name:
        return
    try:
        register_part = str(message.content.split(" ")[1])
        register_cut = str(message.channel.name.split("_")[0])
        register_cut = int(re.sub(r"[^\d]", "", register_cut))
    except:
        return
    try:
        register_person = str(message.content.split(" ")[2])
    except:
        register_person = str(message.author.display_name)
    
    common = Common()
    loadGS = common.loadGS
    loadGS.load_spreadsheet(spreadsheet=common.spreadsheet, 
                            cut_index=register_cut, 
                            target_info="member", 
                            update_info=register_person, 
                            component_index=component_index_reference_dict[register_part]
                            )
    await message.channel.edit(name=f"{register_cut}_{register_person}")
    await message.channel.send(f"{register_person} カット{register_cut} {register_part} を登録します")

@shell_arc_bot.event
async def on_message(message):
    if message.author.display_name != "Shell_Arc_Notice_Center" or message.channel.name != "提出通知センター":
        await shell_arc_bot.process_commands(message)
        return
    notice_content = str(message.content)
    cut_num_matching = re.search(r"カット(\d+?)・", notice_content)
    if cut_num_matching:
        cut_num = cut_num_matching.group(1)
    cut_num = int(cut_num)
    cut_channel = discord.utils.find(lambda c: c.name.startswith(f"{cut_num}_"), message.guild.text_channels)
    print(cut_num)
    print(cut_channel)
    mentioning_role = discord.utils.get(message.guild.roles, name="作画監督")
    if mentioning_role:
        await cut_channel.send(f"{mentioning_role.mention} {notice_content}")
    await shell_arc_bot.process_commands(message)


"""
@shell_arc_bot.event
async def test_action(ctx):
    view = SubmissionSelectionView(timeout=None)
    await ctx.send(view=view)

@shell_arc_bot.command()
async def test(ctx):
    message = ctx.message
    await message.channel.send("テストです")
    await test_action(ctx)
"""

shell_arc_bot.run(TOKEN)
# dc_client.run(TOKEN)

#conda activate null_proj ; cd /Users/shiinaayame/Documents/Shell_Arc_discordbot/discord_bot ; python3 discord_connection.py
