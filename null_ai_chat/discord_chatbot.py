import os
import json
from pathlib import Path

import requests
from dotenv import load_dotenv
import discord
from discord.ext import commands

proj_ctx_dir = Path(os.environ.get("SHELLARC_PROJECT_CTX", None))
load_dotenv(verbose=True)
dotenv_path = proj_ctx_dir / ".env"
if not dotenv_path.exists():
    print(".env file not exist")
    exit()
load_dotenv(dotenv_path)
DIFY_KEY = os.environ.get("Dify_token")
DIFY_BASE_URL = os.environ.get("Dify_baseurl") 
DC_CHATBOT_TOKEN = os.environ.get("Discord_charbot_token")

discord_config_file_path = proj_ctx_dir / "discord_config.json"
if not discord_config_file_path.exists():
    print("discord_config file not exist")
    exit()
with open(discord_config_file_path, mode="r", encoding="utf-8") as config_file:
    discord_config_dict = json.load(config_file)
    config = discord_config_dict
bot_command = config["bot_command"]
shell_arc_chatbot = commands.Bot(command_prefix=bot_command, intents=discord.Intents.all())

async def response_user(q: str,
                  asking_person: str,
                  chat_mode: str
                  ) -> str:
    endpoint = f"{DIFY_BASE_URL}/chat-messages"
    headers = {
        'Authorization': f'Bearer {DIFY_KEY}',
        'Content-Type': 'application/json',
    }
    payload = {
        "inputs": {
            "chat_mode" : chat_mode
        },        
        "query": q,
        "response_mode": "blocking", 
        "conversation_id": "",      
        "user": asking_person,  
    }

    response = requests.post(endpoint, headers=headers, json=payload)
    data = response.json()
    ans = str(data.get('answer'))
    return ans

@shell_arc_chatbot.command()
async def nuru(ctx):
    message = ctx.message
    if message.author.bot:
        return
    message_str = str(message.content)
    message_str = message_str.lstrip("..nuru").strip()
    if not message_str:
        return
    await message.channel.send("考えているぬる...")
    print(message_str)
    sender_name = str(message.author.display_name)
    server_id = str(message.guild.id)
    casual_server = config.get("casual_server", [])
    chat_mode = "casual" if server_id in casual_server else "technical"
    try:
        resp = await response_user(
            q = message_str,
            asking_person=sender_name,
            chat_mode=chat_mode
        )
    except Exception as e:
        print(f"Dify error : {e}")
        return
    await message.channel.send(resp)

shell_arc_chatbot.run(DC_CHATBOT_TOKEN)