import re
import os
import sys
import io
import time
import asyncio
import json
import random
from enum import Enum
from pathlib import Path

import discord
from discord.ext import commands
from discord import Webhook as Webhook
from dotenv import load_dotenv
import gspread

from shellarc_core.process.register import ShellArc_Register
from shellarc_core.process.requesting import ShellArc_Request
from shellarc_core.process.reviewing import ShellArc_Review
from shellarc_core.process.uploader import ShellArc_Upload
from shellarc_core.process.query import ShellArc_Query
from shellarc_core.exception.structure_error import (
    ShellArcError, SA_AuthError, SA_ErrorCode,
    SA_LocalIOError
)
from shellarc_core.exception.user_exception import ShellArcException

from .discord_notice_webhook import DiscordNotice as Notice






load_dotenv(verbose=True)
project_ctx_dir = Path(os.environ.get("SHELLARC_PROJECT_CTX", None))
dotenv_path = project_ctx_dir / ".env"
if not dotenv_path.exists():
    raise SA_AuthError(
        error_log=f"dotenv_path {dotenv_path} not exist",
        error_code=SA_ErrorCode.SA_9001
    )
load_dotenv(dotenv_path)
TOKEN = os.environ.get("Discord_token")
SERVER_ID = os.environ.get("Discord_server_id")
print(SERVER_ID)
dc_client = discord.Client(intents=discord.Intents.all())

#load config
discord_config_file_path = Path(__file__).resolve().parents[1] / 'project_ctx/discord_config.json'
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
bucket_name = config["bucket_name"]

in_zip = ["png"]

shell_arc_bot = commands.Bot(
    command_prefix=bot_command, 
    intents=discord.Intents.all()
    )

def process_cut_num(cut_cluster):
    match = re.search(r'カット(\d+)、?', cut_cluster)
    if match:
        return str(match.group(1))
    return None

class ShellArcActions(Enum):
    UP = 1
    APPR = 2
    DL = 3
    REG = 4
    CAPPR = 5






#SelectionUI

class ShellArcSelectionView(discord.ui.View): 
    def __init__(self, 
                 action: ShellArcActions,
                 timeout: int=120, 
                 message=None,
                 ):
        super().__init__(timeout=timeout)
        self.message = message
        self.action = action

    @discord.ui.select(
        cls=discord.ui.Select,
        placeholder="作業部分を選択してください",
        options=[discord.SelectOption(label=component) for component in component_index_reference_dict]
    )
    async def select(
        self, 
        interaction: discord.Interaction, 
        select: discord.ui.Select
        ):
        await interaction.response.defer()

        message = self.message
        channel_name = str(message.channel.name.lower())
        try:
            processing_cut_cluster = str(channel_name.split(channel_name_divider)[0])
            print(f"submitting_cut_cluster is {processing_cut_cluster}")
            processing_cut = process_cut_num(processing_cut_cluster)
            print(f"submitting_cut is {processing_cut}")
            if processing_cut is None:
                raise ValueError("カット番号の抽出に失敗しました")
            print(f"抽出されたカット番号: {processing_cut}")
            processing_cut = re.sub(r"[^\d]", "", processing_cut)
            processing_cut= int(processing_cut)
            processing_person = str(message.author.display_name)
            processing_component = str(select.values[0])
        except Exception as e:
            print("Error occurred while processing the submission selection")
            print(e)
            return
        
        if self.action == ShellArcActions.DL or self.action == ShellArcActions.CAPPR:
            if self.action == ShellArcActions.CAPPR:
                processing_take = -1
            else:
                try:
                    designated_take = int(message.content.split(" ")[1])
                except:
                    designated_take = 0
                processing_take = designated_take
            shell_arc_bot.dispatch(
                "download_action",
                message,
                processing_cut,
                processing_component,
                processing_take
            )
            return
        elif self.action == ShellArcActions.REG:
            message_cmd = message.content.split(" ")
            force = len(message_cmd) > 1 and message_cmd[1] == "f"
            shell_arc_bot.dispatch(
                "register_action",
                message,
                processing_cut,
                processing_component,
                processing_person,
                force
            )
            return
        if self.action == ShellArcActions.UP:
            confirmation_msg = f"カット{processing_cut}・{processing_component} 提出しますか（はい・いいえ）"
        elif self.action == ShellArcActions.APPR:
            confirmation_msg = "アップを確定しますか（確定c・修正必要d・キャンセル）"
        await interaction.channel.send(confirmation_msg)
        def check(m):
            return m.author == message.author and m.channel == message.channel
        try:
            reply_message = await shell_arc_bot.wait_for('message', check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await message.channel.send("時間超過です。やり直してください")
            return
        except:
            print("Error occurred while waiting for the submission confirmation")

        if self.action == ShellArcActions.UP:
            if reply_message.content == "はい":
                shell_arc_bot.dispatch(
                    "push_action", 
                    message, 
                    processing_cut, 
                    processing_component, 
                    processing_person
                    )
            else:
                await message.channel.send("提出が棄却されました")
        elif self.action == ShellArcActions.APPR:
            if reply_message.content in ["確定", "c", "C"]:
                shell_arc_bot.dispatch(
                    "reviewing_action", 
                    message, 
                    processing_cut, 
                    processing_component, 
                    processing_person,
                    True
                    )
            elif reply_message.content in ["修正必要", "d", "D"]:
                shell_arc_bot.dispatch(
                    "reviewing_action", 
                    message, 
                    processing_cut, 
                    processing_component, 
                    processing_person,
                    False
                    )
            else:
                await message.channel.send("承認プロセスが棄却されました")






#ACTIONS

@shell_arc_bot.event
async def on_push_action(message, 
                         submitting_cut, 
                         submitting_component, 
                         submitting_person
                         ):
    submitting_component_en = component_reference_dict[submitting_component]
    submissions_raw = message.attachments
    try:
        shellarc_upload = ShellArc_Upload(
            cut_num=int(submitting_cut),
            working_component=submitting_component_en,
        )
        read_file_coros = [file.read() for file in submissions_raw] 
        file_data_list = await asyncio.gather(*read_file_coros)
        files = {file.filename : file_bytes for file, file_bytes in zip(submissions_raw, file_data_list)}
        await shellarc_upload.upload_file(
            file=files,
            submitter_name=submitting_person
        )
    except ShellArcException as e:
        await message.channel.send(e.frontend_msg)
    except ShellArcError as e:
        await message.channel.send(e.frontend_msg)
    except Exception as e:
        await message.channel.send(f"UNEXPECTED PYTHON EXCEPTION : {e}")
    mentioning_role = discord.utils.get(message.guild.roles, name=admin_roles["keyframe_qc"])
    await message.channel.send(f"カット{submitting_cut} {submitting_component} が提出されました {mentioning_role.mention}")


@shell_arc_bot.event
async def on_reviewing_action(message, 
                              reviewing_cut, 
                              reviewing_component, 
                              reviewing_person,
                              is_approve
                              ):
    reviewing_component_en = component_reference_dict[reviewing_component]
    try:
        shellarc_review = ShellArc_Review(
            cut_num=int(reviewing_cut),
            reviewing_component=reviewing_component_en
        )
        if is_approve:
            await shellarc_review.approve_action(reviewer_name=reviewing_person)
            await message.channel.send(f"カット{reviewing_cut} {reviewing_component} が確定されました")
        else:
            await shellarc_review.decline_action(reviewer_name=reviewing_person)
            await message.channel.send(f"カット{reviewing_cut} {reviewing_component} がアーカイブされました")
    except ShellArcException as e:
        await message.channel.send(e.frontend_msg)
    except ShellArcError as e:
        await message.channel.send(e.frontend_msg)
    except Exception as e:
        await message.channel.send(f"UNEXPECTED PYTHON EXCEPTION : {e}")
        
    
@shell_arc_bot.event
async def on_download_action(message,
                             requesting_cut,
                             requesting_component,
                             requesting_take
                             ):
    downloaded_path = ""
    requesting_component_en = component_reference_dict[requesting_component]
    try:
        shellarc_request = ShellArc_Request(
            cut_num=int(requesting_cut),
            requesting_component=requesting_component_en
        )
        downloaded_material = await shellarc_request.download_material(requesting_take=requesting_take)
        downloaded_path = downloaded_material[0]
        downloaded_filename = downloaded_material[1]
        if not Path(downloaded_path).exists():
            raise SA_LocalIOError(
                error_log="generated temp download path not exist",
                error_code=SA_ErrorCode.SA_8000
            )
        if requesting_take > 1:
            take_name = f"テイク{requesting_take}"
        else:
            take_name = "最新テイク" if requesting_take == 0 else "作業中テイク"
        await message.channel.send(
            f"カット{requesting_cut} {take_name} {requesting_component} が取得されました",
            file=discord.File(downloaded_path), 
            filename=downloaded_filename
            )
    except ShellArcException as e:
        await message.channel.send(e.frontend_msg)
    except ShellArcError as e:
        await message.channel.send(e.frontend_msg)
    except Exception as e:
        await message.channel.send(f"UNEXPECTED PYTHON EXCEPTION : {e}")
    finally:
        if Path(downloaded_path).exists():
            os.unlink(downloaded_path)

    
@shell_arc_bot.event
async def on_register_action(message,
                             registering_cut,
                             registering_component,
                             registering_person,
                             force
                             ):
    rregistering_component_en = component_reference_dict[registering_component]
    try:
        shellarc_register = ShellArc_Register()
        await shellarc_register.register_work(
            registering_person=registering_person,
            registering_component=rregistering_component_en,
            registering_cut=registering_cut,
            force=force
        )
    except ShellArcException as e:
        await message.channel.send(e.frontend_msg)
    except ShellArcError as e:
        await message.channel.send(e.frontend_msg)
    except Exception as e:
        await message.channel.send(f"UNEXPECTED PYTHON EXCEPTION : {e}")
    current_channel_name = message.channel.name.split(channel_name_divider)
    if len(current_channel_name) > 1:
        current_channel_name[1] = registering_person
    else:
        current_channel_name.append(registering_person)
    new_channel_name = channel_name_divider.join(current_channel_name)
    await message.channel.edit(name=new_channel_name)
    await message.channel.send(f"{registering_person}をカット{registering_cut} {registering_component}に登録しました")
    





#Commands with cloud communication

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
    view = ShellArcSelectionView(
        action=ShellArcActions.UP, 
        timeout=60, 
        message=message
        )
    await ctx.send(view=view)


@shell_arc_bot.command()
async def appr(ctx):
    message = ctx.message
    if message.author.bot:
        return
    if channel_name_divider not in message.channel.name:
        return
    view = ShellArcSelectionView(
        action=ShellArcActions.APPR, 
        timeout=60, 
        message=message
        )
    await ctx.send(view=view)


@shell_arc_bot.command()
async def dl(ctx):
    message = ctx.message
    if message.author.bot:
        return
    if channel_name_divider not in message.channel.name:
        return
    view = ShellArcSelectionView(
        action=ShellArcActions.DL,
        timeout=60,
        message=message
    )
    await ctx.send(view=view)


@shell_arc_bot.command()
async def check(ctx):
    message = ctx.message
    if message.author.bot:
        return
    if channel_name_divider not in message.channel.name:
        return
    view = ShellArcSelectionView(
        action=ShellArcActions.CAPPR,
        timeout=60,
        message=message
    )
    await ctx.send(view=view)


@shell_arc_bot.command()
async def reg(ctx):
    print("regコマンドが実行されました")
    message = ctx.message
    if message.author.bot:
        return
    view = ShellArcSelectionView(
        action=ShellArcActions.REG,
        timeout=60,
        message=message
    )
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
    shellarc_query = ShellArc_Query()
    query_result = shellarc_query.efficient_get_spreadsheet_info(
        target_index_value=asking_person,
        index_info_types=[f"{c}_PIC" for c, _ in component_index_reference_dict.items()],
        target_info_types=["cut_num", "cut_num", "cut_num", "cut_num", "cut_num"],
        search_range=[1, TOTAL_CUT_COUNT]
    )
    output_msg = asking_person
    for k, v in query_result.items():
        output_msg += f"\nカット{v} {k.split("_")[0]}"
    await message.reply(output_msg)



# @shell_arc_bot.command()
# async def build_project_server(ctx):
#     message = ctx.message
#     if message.author.bot:
#         return
#     author_roles = [role.name for role in message.author.roles]
#     if "SETTER_ADMIN" not in author_roles or message.channel.name != "build_channel":
#         await message.channel.send("\"build_channel\"という名前を持つチャンネルを作成し、\"SETTER_ADMIN\"という名前のロールを設定者に付与してください")
#         return
    
#     Category = await ctx.guild.create_category(submission_channel_catagory_name)
#     await Category.create_text_channel(center_channel_names["notice_center"])
#     await Category.create_text_channel(center_channel_names["schedule_query_center"])

#     for count in range(1, TOTAL_CUT_COUNT+1):
#         if count in linker_children_set:
#             continue
#         child_cut = linkp.trace_to_child(count)
#         if child_cut is not None:
#             child_text = "、".join([str(i) for i in child_cut])
#             child_text = str(count) + "、" + child_text
#         else: 
#             child_text = str(count)
#         await Category.create_text_channel(f"{child_text}{channel_name_divider}")
#         if count % 5 == 0:
#             time.sleep(1.5)

#     await message.channel.send("設定完了です\n\"BUILD_CHANNEL\"チャンネルと\"SETTER_ADMIN\"ロールを削除してください")

# @shell_arc_bot.event
# async def on_message(message):
#     if message.author == shell_arc_bot.user:
#         return
#     if message.author.display_name != webhook_bot_name or \
#         message.channel.name != center_channel_names["notice_center"]:
#         await shell_arc_bot.process_commands(message)
#         return
#     print("notice_centerにメッセージが投稿されました")
#     notice_content = str(message.content)
#     cut_num_matching = re.search(notice_message_cut_extraction_regex, notice_content)
#     if cut_num_matching:
#         cut_num = cut_num_matching.group(1)
#     cut_num = int(cut_num)
#     re_pattern = re.compile(r'カット(\d+)、')
#     cut_channel = discord.utils.find(
#         lambda c: (m := re_pattern.search(c.name)) and m.group(1) == str(cut_num),
#         message.guild.text_channels)
#     mentioning_role = discord.utils.get(message.guild.roles, name=admin_roles["keyframe_qc"])
#     if mentioning_role:
#         await cut_channel.send(f"{mentioning_role.mention} {notice_content}")
#     await shell_arc_bot.process_commands(message)

@shell_arc_bot.event
async def on_ready():
    print("ログインしました")

@shell_arc_bot.command()
async def testarc(ctx):
    message = ctx.message
    if message.author.bot:
        return
    await message.reply("MyReply")

shell_arc_bot.run(TOKEN)