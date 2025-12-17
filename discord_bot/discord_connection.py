import re
import os
import sys
import io
import asyncio

import discord
from dotenv import load_dotenv

proj_root = os.path.dirname(os.path.abspath(__file__))
if proj_root not in sys.path:
    sys.path.append(proj_root)

from backend.request_r2 import Cloudflare_R2_service as R2
from backend.common_initialisation import CommonInitialisation as Common
from backend.file_operation import FileOperation as FileOp

load_dotenv(verbose=True)
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)
TOKEN = os.environ.get("Discord_token")
SERVER_ID = os.environ.get("Discord_server_id")
dc_client = discord.Client(intents=discord.Intents.all())

component_reference_dict = {
    "genga" : "原画",
    "nakawari" : "中割り", 
    "haikei" : "背景",
    "satsuei" : "撮影",
    "hennsyu" : "編集"
}

@dc_client.event
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

    # if work_data["temporary"]["naming"] != None:
    #     temporary = {"naming": renamed, "cut": submitting_cut, "take": current_take, "creator": str(submitting_person), "reviewer": None, "comments": None}
    #     structure = fileop.update_database(current_take=current_take, work_data=work_data, temporary=temporary, non_active=work_data["temporary"])
    # else:
    #     temporary = {"naming": renamed, "cut": submitting_cut, "take": current_take, "creator": str(submitting_person), "reviewer": None, "comments": None}
    #     structure = fileop.update_database(current_take=current_take, work_data=work_data, temporary=temporary)
    # ref_work_obj.update(structure)

    r2 = R2(common.s3_client)
    r2.upload_file(submission, f"{proj_setting_data['collection_name']}/cut{submitting_cut:02}/{working_component}/{renamed}.{required_format[0]}")

    loadGS.load_spreadsheet(spreadsheet=spreadsheet, cut_index=submitting_cut, target_info="member", update_info=submitting_person, component_index=working_index)
    loadGS.load_spreadsheet(spreadsheet=spreadsheet, cut_index=submitting_cut, target_info="situation", update_info="作業中", component_index=working_index)

    await message.channel.send(f"カット{submitting_cut}・{submitting_component} にプッシュしました")

@dc_client.event
async def on_ready():
    print("ログインしました")

@dc_client.event
async def push_action(message, submitting_cut, submitting_component):
    submitting_person = str(message.author.display_name)
    submitting_component = component_reference_dict[submitting_component]
    submission_raw = message.attachments[0]
    await submit_file(message, submitting_person, submitting_cut, submitting_component, submission_raw)

@dc_client.event
async def approve_action(message, num, part):
    await message.channel.send(f"カット{num}・{part} を許可します")

@dc_client.event
async def on_message(message):
    if message.author.bot:
        return
    
    if re.fullmatch(r"..push>\d+>[a-z]+", message.content) != None:
        if not message.attachments:
            await message.channel.send("ファイルを添付してからプッシュしてくださいください")
            return
        submitting_cut = int(message.content.split(">")[1])
        submitting_component = str(message.content.split(">")[2])
        await message.channel.send("プッシュしますか（はい・いいえ）")
        def check(m):
            return m.author == message.author and m.channel == message.channel
        try:
            reply_message = await dc_client.wait_for('message', check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await message.channel.send("時間超過です。やり直してください")
        if reply_message.content == "はい":
            await push_action(message, submitting_cut, submitting_component)

dc_client.run(TOKEN)

#conda activate null_proj ; cd /Users/shiinaayame/Documents/Shell_Arcのコピー ; python3 discord_connection.py
