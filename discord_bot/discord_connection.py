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
discord_config_file_path = project_ctx_dir / 'project_ctx/discord_config.json'
with open(discord_config_file_path, mode="r", encoding="utf-8") as config_file:
    discord_config_dict = json.load(config_file)
    config = discord_config_dict

TOTAL_CUT_COUNT = config["total_cut_count"]
webhook_bot_name = config["webhook_bot_name"]
cut_extraction_regex = config["notice_message_cut_extraction_regex"]
submission_channel_catagory_name = config["submission_channel_catagory_name"]
channel_name_divider = config.get("channel_name_divider", "_")
bot_command = config.get("bot_command", "..")
component_name_e2j = config["component_reference"]
component_name_j2e = {v : k for k, v in component_name_e2j.items()}
admin_roles = config["admin_roles"]
shellarc_center = config["center_channel_names"]



shell_arc_bot = commands.Bot(
    command_prefix=bot_command, 
    intents=discord.Intents.all()
    )

def process_cut_num(cut_cluster):
    match = re.search(cut_extraction_regex, cut_cluster)
    if match:
        return str(match.group(1))
    return None

class ShellArcActions(Enum):
    UP = 1
    APPR = 2
    DL = 3
    REG = 4
    CAPPR = 5

class ShellArcEvents(Enum):
    DL_Event = "download_action"
    REG_Event = "register_action"
    UP_Event = "push_action"
    APPR_Event = "reviewing_action"






class ShellArcButton(discord.ui.Button):
    def __init__(self, 
                 label: str,
                 style: discord.ButtonStyle,
                 sa_action: ShellArcActions,
                 info: dict,
                 message: discord.Message
                 ):
        super().__init__(
            label=label,
            style=style
            )
        self.sa_action = sa_action
        self.info = info
        self.message = message
        
    async def callback(self, 
                       interaction: discord.Interaction
                       ):
        await interaction.response.defer(ephemeral=True)
        if self.sa_action == ShellArcActions.UP:
            if self.label == "はい":
                shell_arc_bot.dispatch(
                    ShellArcEvents.UP_Event.value,
                    interaction,
                    self.message,
                    self.info["processing_cut"],
                    self.info["processing_component"],
                    self.info["processing_person"]
                )
            else:
                await interaction.edit_original_response(content="提出プロセスが棄却されました", view=None)
        elif self.sa_action == ShellArcActions.APPR:
            if self.label == "確定":
                shell_arc_bot.dispatch(
                    ShellArcEvents.APPR_Event.value,
                    interaction,
                    self.message,
                    self.info["processing_cut"],
                    self.info["processing_component"],
                    self.info["processing_person"],
                    True
                )
            elif self.label == "要修正":
                shell_arc_bot.dispatch(
                    ShellArcEvents.APPR_Event.value,
                    interaction,
                    self.message,
                    self.info["processing_cut"],
                    self.info["processing_component"],
                    self.info["processing_person"],
                    False
                )
            else:
                await interaction.edit_original_response(content="承認プロセスが棄却されました", view=None)


class ShellArcButtonView(discord.ui.View):
    def __init__(self,
                 options: dict[str, discord.ButtonStyle], 
                 sa_action: ShellArcActions,
                 info: dict,
                 message: discord.Message,
                 timeout: int=30
                 ):
        super().__init__(timeout=timeout)
        for option, style in options.items():
            self.add_item(ShellArcButton(label=option, style=style, sa_action=sa_action, info=info, message=message))


class ShellArcDropdown(discord.ui.Select):
    def __init__(self,
                 options,
                 sa_action: ShellArcActions,
                 message: discord.Message
                 ):
        super().__init__(
            placeholder="作業工程を選択してください", 
            min_values=1, 
            max_values=1, 
            options=options
            )
        self.sa_action = sa_action
        self.message = message

    async def callback(self, 
                       interaction: discord.Interaction
                       ):
        channel_name = str(interaction.channel.name.lower())
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
            processing_person = str(interaction.user.display_name)
            processing_component = str(self.values[0])
        except Exception as e:
            print("Error occurred while processing the submission selection")
            print(e)
            return
        
        await interaction.response.defer(ephemeral=True)
        if self.sa_action in [ShellArcActions.DL, ShellArcActions.CAPPR, ShellArcActions.REG]:
            if self.sa_action == ShellArcActions.CAPPR or self.sa_action == ShellArcActions.DL:
                if self.sa_action == ShellArcActions.CAPPR:
                    processing_take = "-1"
                elif self.sa_action == ShellArcActions.DL:
                    try:
                        processing_take = str(self.message.content.split(" ")[1])
                    except:
                        processing_take = "0"
                shell_arc_bot.dispatch(
                    ShellArcEvents.DL_Event.value,
                    interaction,
                    processing_cut,
                    processing_component,
                    processing_take
                )
            elif self.sa_action == ShellArcActions.REG:
                is_force = len(self.message.content.split(" ")) > 1 and self.message.content.split(" ")[1] == "f"
                shell_arc_bot.dispatch(
                    ShellArcEvents.REG_Event.value,
                    interaction,
                    processing_cut,
                    processing_component,
                    processing_person,
                    is_force
                )
        elif self.sa_action in [ShellArcActions.UP, ShellArcActions.APPR]:
            if self.sa_action == ShellArcActions.UP:
                confirmation_kw = "提出" 
                confirmation_options = {
                    "はい" : discord.ButtonStyle.success,
                    "いいえ": discord.ButtonStyle.red
                    }
            elif self.sa_action == ShellArcActions.APPR:
                confirmation_kw = "確定" 
                confirmation_options = {
                    "確定" : discord.ButtonStyle.success, 
                    "要修正" : discord.ButtonStyle.red, 
                    "キャンセル" : discord.ButtonStyle.gray
                    }
            info = {
                "processing_cut" : processing_cut,
                "processing_component" : processing_component,
                "processing_person" : processing_person
            }
            await interaction.edit_original_response(
                content=f"カット{processing_cut}・{processing_component} を{confirmation_kw}しますか",
                view=ShellArcButtonView(options=confirmation_options, sa_action=self.sa_action, info=info, message=self.message)
                )


class ShellArcDropdownView(discord.ui.View):
    def __init__(self,
                 sa_action: ShellArcActions,
                 message: discord.Message
                 ):
        super().__init__()
        channel_name = str(message.channel.name.lower())
        try:
            processing_cut_cluster = str(channel_name.split(channel_name_divider)[0])
            processing_cut = process_cut_num(processing_cut_cluster)
            print(f"submitting_cut is {processing_cut}")
        except Exception as e:
            print(f"Error occurred while processing the submission selection : {e}")
            return
        component_enname_ls = ShellArc_Query.get_components_enname(cut_num=int(processing_cut))
        options=[discord.SelectOption(label=component_name_e2j.get(component_en, component_en)) for component_en in component_enname_ls]
        self.add_item(ShellArcDropdown(options=options, sa_action=sa_action, message=message))







#ACTIONS

@shell_arc_bot.event
async def on_push_action(interaction: discord.Interaction, 
                         message: discord.Message,
                         submitting_cut, 
                         submitting_component, 
                         submitting_person
                         ):
    submitting_component_en = component_name_j2e.get(submitting_component, submitting_component)
    submissions_raw = message.attachments
    git_message = message.content.split(" ")[1] if len(message.content.split(" ")) > 1 else ""
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
            submitter_name=submitting_person,
            message=git_message
        )
    except ShellArcException as e:
        await interaction.edit_original_response(content=e.frontend_msg, view=None)
        return
    except ShellArcError as e:
        await interaction.edit_original_response(content=e.frontend_msg, view=None)
        return
    except Exception as e:
        await interaction.edit_original_response(content=f"UNEXPECTED PYTHON EXCEPTION : {e}", view=None)
        return
    
    confirm_msg = f"カット{submitting_cut} {submitting_component} が提出されました"
    for keyframe_qc in admin_roles.get("keyframe_qc", []):
        mentioning_role = discord.utils.get(message.guild.roles, name=keyframe_qc)
        confirm_msg += f" {mentioning_role.mention}"
    await interaction.edit_original_response(content=confirm_msg, view=None)


@shell_arc_bot.event
async def on_reviewing_action(interaction: discord.Interaction, 
                              message: discord.Message,
                              reviewing_cut, 
                              reviewing_component, 
                              reviewing_person,
                              is_approve
                              ):
    reviewing_component_en = component_name_j2e.get(reviewing_component, reviewing_component)
    git_message = message.content.split(" ")[1] if len(message.content.split(" ")) > 1 else ""
    try:
        shellarc_review = ShellArc_Review(
            cut_num=int(reviewing_cut),
            reviewing_component=reviewing_component_en
        )
        await shellarc_review.pending_action(
            reviewer_name=reviewing_person,
            is_approve=is_approve,
            message=git_message
        )
        if is_approve:
            await interaction.edit_original_response(content=f"カット{reviewing_cut} {reviewing_component} が確定されました", view=None)
        else:
            await interaction.edit_original_response(content=f"カット{reviewing_cut} {reviewing_component} がアーカイブされました", view=None)
    except ShellArcException as e:
        await interaction.edit_original_response(content=e.frontend_msg, view=None)
        return
    except ShellArcError as e:
        await interaction.edit_original_response(content=e.frontend_msg, view=None)
        return
    except Exception as e:
        await interaction.edit_original_response(content=f"UNEXPECTED PYTHON EXCEPTION : {e}", view=None)
        return
        
    
@shell_arc_bot.event
async def on_download_action(interaction: discord.Interaction,
                             requesting_cut,
                             requesting_component,
                             requesting_take
                             ):
    downloaded_path = ""
    requesting_component_en = component_name_j2e.get(requesting_component, requesting_component)
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
        await interaction.edit_original_response(content=f"カット{requesting_cut} {take_name} {requesting_component} を取得中", view=None)
        await interaction.channel.send(
            f"カット{requesting_cut} {take_name} {requesting_component} が取得されました",
            file=discord.File(downloaded_path), 
            filename=downloaded_filename
            )
    except ShellArcException as e:
        await interaction.edit_original_response(content=e.frontend_msg, view=None)
        return
    except ShellArcError as e:
        await interaction.edit_original_response(content=e.frontend_msg, view=None)
        return
    except Exception as e:
        await interaction.edit_original_response(content=f"UNEXPECTED PYTHON EXCEPTION : {e}", view=None)
        return
    finally:
        if Path(downloaded_path).exists():
            os.unlink(downloaded_path)

    
@shell_arc_bot.event
async def on_register_action(interaction: discord.Interaction,
                             registering_cut,
                             registering_component,
                             registering_person,
                             force
                             ):
    registering_component_en = component_name_j2e.get(registering_component, registering_component)
    try:
        shellarc_register = ShellArc_Register()
        await shellarc_register.register_work(
            registering_person=registering_person,
            registering_component=registering_component_en,
            registering_cut=registering_cut,
            force=force
        )
    except ShellArcException as e:
        await interaction.edit_original_response(content=e.frontend_msg, view=None)
        return
    except ShellArcError as e:
        await interaction.edit_original_response(content=e.frontend_msg, view=None)
        return
    except Exception as e:
        await interaction.edit_original_response(content=f"UNEXPECTED PYTHON EXCEPTION : {e}", view=None)
        return

    current_channel_name = interaction.channel.name.split(channel_name_divider)
    if len(current_channel_name) > 1:
        current_channel_name[1] = registering_person
    else:
        current_channel_name.append(registering_person)
    new_channel_name = channel_name_divider.join(current_channel_name)
    await interaction.channel.edit(name=new_channel_name)
    await interaction.edit_original_response(content=f"{registering_person}をカット{registering_cut} {registering_component}に登録しました", view=None)
    





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
    view = ShellArcDropdownView(
        sa_action=ShellArcActions.UP,
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
    view = ShellArcDropdownView(
        sa_action=ShellArcActions.APPR,
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
    view = ShellArcDropdownView(
        sa_action=ShellArcActions.DL,
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
    view = ShellArcDropdownView(
        sa_action=ShellArcActions.CAPPR,
        message=message
    )
    await ctx.send(view=view)


@shell_arc_bot.command()
async def reg(ctx):
    message = ctx.message
    if message.author.bot:
        return
    view = ShellArcDropdownView(
        sa_action=ShellArcActions.REG,
        message=message
    )
    await ctx.send(view=view)


@shell_arc_bot.command()
async def history(ctx):
    message = ctx.message
    if message.author.bot:
        return
    channel_name = str(message.channel.name.lower())
    message_command = message.content.split(" ")
    if len(message_command) < 2:
        await message.channel.send("作業工程を指定してください")
        return
    quering_component = message_command[1]
    quering_component = component_name_j2e.get(quering_component, quering_component)
    try:
        quering_cut_cluster = str(channel_name.split(channel_name_divider)[0])
        quering_cut = int(process_cut_num(quering_cut_cluster))
        print(f"submitting_cut is {quering_cut}")
    except Exception as e:
        print(f"Error occurred while processing the submission selection : {e}")
        return
    if len(message_command) == 3:
        try:
            max_length = int(message_command[2])
        except:
            max_length = None
    history_dict = ShellArc_Query.get_history(
        cut_num=quering_cut,
        component=quering_component,
        max_length=max_length
    )
    reply_text = ""
    for commit_id, commit_content in history_dict:
        reply_text += f"{commit_id} - {commit_content}\n"
    await message.channel.send(reply_text)


@shell_arc_bot.command()
async def ask(ctx):
    message = ctx.message
    if message.author.bot:
        return
    if message.channel.name != shellarc_center["schedule_query_center"]:
        return
    try:
        asking_person = str(message.content.split(" ")[1])
    except:
        asking_person = str(message.author.display_name)
    await message.reply("検索中...\n10秒ほどお待ちいただく場合があります")
    shellarc_query = ShellArc_Query()
    query_result = shellarc_query.efficient_get_spreadsheet_info(
        target_index_value=asking_person,
        index_info_types=[f"{c}_PIC" for c in component_name_e2j],
        target_info_types=["cut_num", "cut_num", "cut_num", "cut_num", "cut_num"],
        search_range=[1, TOTAL_CUT_COUNT]
    )
    output_msg = asking_person
    for k, v in query_result.items():
        output_msg += f"\nカット{v} {k.split('_')[0]}"
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