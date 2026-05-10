import re
import os
import sys
import io
import time
import asyncio
import json
import random
from pathlib import Path

import discord
from discord.ext import commands
from discord import Webhook as Webhook
from dotenv import load_dotenv
import gspread

proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if proj_root not in sys.path:
    sys.path.append(proj_root)

from backend.request_r2 import Cloudflare_R2_service as R2
from backend.common_initialisation import CommonInitialisation as Common
from backend.file_operation import FileOperation as FileOp
from backend.linker_parser import LinkerParser as LinkP
from discord_notice_webhook import DiscordNotice as Notice

load_dotenv(verbose=True)
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)
TOKEN = os.environ.get("Discord_token")
SERVER_ID = os.environ.get("Discord_server_id")
print(SERVER_ID)
dc_client = discord.Client(intents=discord.Intents.all())

#load config
discord_config_file_path = Path(__file__).parent / "discord_config.json"
with open(discord_config_file_path, mode="r", encoding="utf-8") as config_file:
    discord_config_dict = json.load(config_file)
    config = discord_config_dict

TOTAL_CUT_COUNT = config["total_cut_count"]
component_reference_dict = config["component_reference"]
component_index_reference_dict = config["component_index_reference"]
rev_component_index_reference_dict = {v: k for k, v in component_index_reference_dict.items()}
admin_roles = config["admin_roles"]
center_channel_names = config["center_channel_names"]
webhook_bot_name = config["webhook_bot_name"]
notice_message_cut_extraction_regex = config["notice_message_cut_extraction_regex"]
submission_channel_catagory_name = config["submission_channel_catagory_name"]
channel_name_divider = config["channel_name_divider"]
bot_command = config["bot_command"]

shell_arc_bot = commands.Bot(command_prefix=bot_command, intents=discord.Intents.all())

def process_cut_num(cut_cluster):
    match = re.search(r'カット(\d+)、?', cut_cluster)
    if match:
        return str(match.group(1))
    return None

class SubmissionSelectionView(discord.ui.View): 
    def __init__(self, timeout=120, message=None):
        super().__init__(timeout=timeout)
        self.message = message

    @discord.ui.select(
        cls=discord.ui.Select,
        placeholder="提出する部分を選択してください",
        options=[discord.SelectOption(label=component) for component in component_index_reference_dict]
    )
    async def select(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer()

        message = self.message
        channel_name = str(message.channel.name.lower())
        try:
            submitting_cut_cluster = str(channel_name.split(channel_name_divider)[0])
            print(f"submitting_cut_cluster is {submitting_cut_cluster}")
            submitting_cut = process_cut_num(submitting_cut_cluster)
            print(f"submitting_cut is {submitting_cut}")
            if submitting_cut is None:
                raise ValueError("カット番号の抽出に失敗しました")
            #submitting_cut = re.sub(r"[^\d]", "", submitting_cut)
            print(f"抽出されたカット番号: {submitting_cut}")
            submitting_cut = int(submitting_cut)
            submitting_person = str(channel_name.split(channel_name_divider)[1])
            submitting_component = str(select.values[0])
        except Exception as e:
            print("Error occurred while processing the submission selection")
            print(e)
            return

        if submitting_person != "" and submitting_person != str(message.author.display_name):
            await message.channel.send("Warning : 提出者アカウント名はチャンネルで指定された担当者名と異なります")
            submitting_person = str(message.author.display_name)
        await interaction.channel.send(f"カット{submitting_cut}・{submitting_component} 提出しますか（はい・いいえ）")
        def check(m):
            return m.author == message.author and m.channel == message.channel
        try:
            reply_message = await shell_arc_bot.wait_for('message', check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await message.channel.send("時間超過です。やり直してください")
            return
        except:
            print("Error occurred while waiting for the submission confirmation")
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
        placeholder="チェックする部分を選択してください",
        options=[discord.SelectOption(label=component) for component in component_index_reference_dict]
    )
    async def select(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer()

        message = self.message
        channel_name = str(message.channel.name.lower())
        try:
            reviewing_cut_cluster = str(channel_name.split(channel_name_divider)[0])
            reviewing_cut = process_cut_num(reviewing_cut_cluster)
            if reviewing_cut is None:
                raise ValueError("カット番号の抽出に失敗しました")
            reviewing_cut = re.sub(r"[^\d]", "", reviewing_cut)
            reviewing_cut = int(reviewing_cut)
            reviewing_person = str(message.author.display_name)
            reviewing_component = str(select.values[0])
        except:
            print("Error occurred while processing the review selection")
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
    common = Common(uninit=["setting_db"], exclude_init_confirm=True)
    fileop = FileOp()

    #access firebase database
    proj_setting_data = common.proj_setting_data #project setting data dictionary
    ref_collection = common.ref_collection #project main data referncer

    #access spreadsheet
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

    loadGS.load_spreadsheet(cut_index=submitting_cut,
                            target_info="member",
                            update_info=submitting_person,
                            component_index=working_index
                            )
    
    loadGS.load_spreadsheet(cut_index=submitting_cut,
                            target_info="situation",
                            update_info="作業中",
                            component_index=working_index)
    
    mentioning_role = discord.utils.get(message.guild.roles, name=admin_roles["keyframe_qc"])
    await message.channel.send(f"カット{submitting_cut}・{submitting_component} にアップロードしました {mentioning_role.mention}")
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
        loadGS.load_progress(component_index=working_index, is_get=False, total_cut_number=cut_num)
        ref_setting_obj.update({f"component{working_index}.progress" : current_progress})

    loadGS.load_spreadsheet(cut_index=reviewing_cut,
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
    if message.author.bot:
        return
    if channel_name_divider not in message.channel.name:
        return
    if not message.attachments:
        await message.channel.send("ファイルを添付してから提出してください")
        return
    view = SubmissionSelectionView(timeout=None, message=message)
    await ctx.send(view=view)

@shell_arc_bot.command()
async def appr(ctx):
    message = ctx.message
    if message.author.bot:
        return
    if channel_name_divider not in message.channel.name:
        return
    view = ReviewSelectionView(timeout=None, message=message)
    await ctx.send(view=view)

@shell_arc_bot.command()
async def ask(ctx):
    message = ctx.message
    if message.author.bot:
        return
    if message.channel.name != center_channel_names["schedule_query_center"]:
        return
    try:
        asking_person = str(message.content.split(" ")[1])
    except:
        asking_person = str(message.author.display_name)
    await message.reply("検索中...\n10秒ほどお待ちいただく場合があります")
    common = Common(uninit=["r2", "project_db", "setting_db"], exclude_init_confirm=True)
    loadGS = common.loadGS
    spreadsheet_cache = loadGS.spreadsheet_cache
    scheduled_work_list = []
    escaped_divider = re.escape(channel_name_divider)
    re_pattern = re.compile(r'カット(\d+)、')
    for cut_num in range(1, TOTAL_CUT_COUNT+1):
        for part_num in range(1, len(component_index_reference_dict)+1):
            person_incharge = loadGS.efficient_get_spreadsheet(
                current_spreadsheet_cache=spreadsheet_cache, 
                cut_index=cut_num, 
                target_info="member",
                component_index=part_num
            )
            person_incharge = str(person_incharge)
            if person_incharge == asking_person:
                cut_channel = discord.utils.find(
                    lambda c: (m := re_pattern.search(c.name)) and m.group(1) == str(cut_num),
                    message.guild.text_channels)
                scheduled_work_list.append(f"カット{cut_num} {rev_component_index_reference_dict[part_num-1]} <#{cut_channel.id}>")
                
    query_answer_message = f"{asking_person} : "
    if scheduled_work_list:
        for scheduled_work in scheduled_work_list:
            query_answer_message += f"\n{scheduled_work}"
    else:
        query_answer_message += "担当作業がありません"
    await message.reply(query_answer_message)

@shell_arc_bot.command()
async def omikuji(ctx):
    print("omikuji")
    message = ctx.message
    if message.author.bot:
        return
    omikuji_ls = ["大吉", "吉", "小吉", "半吉", "大吉", "吉", "小吉", "半吉", "大吉", "吉", "小吉", "半吉", "ぬるたろうのお守り"]
    picked = str(random.choice(omikuji_ls))
    await message.channel.send(f"{picked} !")


@shell_arc_bot.command()
async def reg(ctx):
    print("regコマンドが実行されました")
    message = ctx.message
    if message.author.bot:
        return
    # if channel_name_divider not in message.channel.name:
    #     print("regコマンドが実行されましたが、チャンネル名に区切り文字が含まれていません")
    #     return
    try:
        register_part_raw = str(message.content.split(" ")[1])
    except:
        register_part_raw_list = [part for part in component_index_reference_dict.keys()]
        register_part_raw = ",".join(register_part_raw_list)
    finally:
        register_cut_cluster = str(message.channel.name.split(channel_name_divider)[0])
        register_cut = process_cut_num(register_cut_cluster)
        register_cut = int(re.sub(r"[^\d]", "", register_cut))
    try:
        register_person = str(message.content.split(" ")[2])
    except:
        register_person = str(message.author.display_name)
    await message.channel.edit(name=f"{register_cut_cluster}{channel_name_divider}{register_person}")
    
    common = Common(uninit=["r2", "project_db", "setting_db"], exclude_init_confirm=True)
    loadGS = common.loadGS
    register_parts_input = register_part_raw.split(",")
    register_parts = []
    for part_input in register_parts_input:
        part_input = part_input.strip()
        part = component_reference_dict.get(part_input, None)
        if part is not None:
            register_parts.append(part)
    for register_part in register_parts:
        if register_part is None:
            continue
        loadGS.load_spreadsheet(cut_index=register_cut, 
                                target_info="member", 
                                update_info=register_person, 
                                component_index=component_index_reference_dict[register_part]+1
                                )
    registed_parts_text = "、".join(register_parts)
    await message.channel.send(f"{register_person} カット{register_cut} {registed_parts_text} を登録します")

@shell_arc_bot.command()
async def build_project_server(ctx):
    message = ctx.message
    if message.author.bot:
        return
    author_roles = [role.name for role in message.author.roles]
    if "SETTER_ADMIN" not in author_roles or message.channel.name != "build_channel":
        await message.channel.send("\"build_channel\"という名前を持つチャンネルを作成し、\"SETTER_ADMIN\"という名前のロールを設定者に付与してください")
        return
    
    Category = await ctx.guild.create_category(submission_channel_catagory_name)
    await Category.create_text_channel(center_channel_names["notice_center"])
    await Category.create_text_channel(center_channel_names["schedule_query_center"])
    linkp = LinkP()
    linker_children_set = linkp.find_children()
    for count in range(1, TOTAL_CUT_COUNT+1):
        if count in linker_children_set:
            continue
        child_cut = linkp.trace_to_child(count)
        if child_cut is not None:
            child_text = "、".join([str(i) for i in child_cut])
            child_text = str(count) + "、" + child_text
        else: 
            child_text = str(count)
        await Category.create_text_channel(f"{child_text}{channel_name_divider}")
        if count % 5 == 0:
            time.sleep(1.5)

    await message.channel.send("設定完了です\n\"BUILD_CHANNEL\"チャンネルと\"SETTER_ADMIN\"ロールを削除してください")

@shell_arc_bot.event
async def on_message(message):
    if message.author == shell_arc_bot.user:
        return
    if message.author.display_name != webhook_bot_name or message.channel.name != center_channel_names["notice_center"]:
        await shell_arc_bot.process_commands(message)
        return
    print("notice_centerにメッセージが投稿されました")
    notice_content = str(message.content)
    cut_num_matching = re.search(notice_message_cut_extraction_regex, notice_content)
    if cut_num_matching:
        cut_num = cut_num_matching.group(1)
    cut_num = int(cut_num)
    escaped_divider = re.escape(channel_name_divider)
    re_pattern = re.compile(r'カット(\d+)、')
    cut_channel = discord.utils.find(
        lambda c: (m := re_pattern.search(c.name)) and m.group(1) == str(cut_num),
        message.guild.text_channels)
    print(cut_num)
    print(cut_channel)
    print("****")
    mentioning_role = discord.utils.get(message.guild.roles, name=admin_roles["keyframe_qc"])
    if mentioning_role:
        await cut_channel.send(f"{mentioning_role.mention} {notice_content}")
    await shell_arc_bot.process_commands(message)

    

#テスト用コード
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
# @shell_arc_bot.command()
# async def test(ctx):
#     message = ctx.message
#     if message.author.bot:
#         return
#     await message.reply("MyReply")


# dc_client.run(TOKEN)

#conda activate null_proj ; cd /Users/shiinaayame/Documents/Shell_Arc_discordbot/discord_bot ; python3 discord_connection.py


shell_arc_bot.run(TOKEN)