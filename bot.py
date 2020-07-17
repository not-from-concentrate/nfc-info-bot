# bot.py
import os, discord, urllib.request, json
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
COMMAND_URL = os.getenv('COMMAND_URL')

command_data = {}
command_embeds = {}
dm_embeds = {}
command_list_embed = {}

def update_commands():
    global command_data, command_embeds, dm_embeds, command_list_embed
    with urllib.request.urlopen(COMMAND_URL) as url:
        command_data = json.loads(url.read().decode())

    command_list_embed = discord.Embed(title="Command List", color=0x0099ff)
    for cmd in command_data:
        cmd_data = command_data[cmd]
        if cmd_data["dm"]:
            command_list_embed.add_field(name=cmd+" [@username]", value=cmd_data["info"], inline=True)
        else:
            command_list_embed.add_field(name=cmd, value=cmd_data["info"], inline=True)
        
        command_embeds[cmd] = discord.Embed(title=cmd_data["title"], color=cmd_data["color"], description=cmd_data["description"])
        dm_embeds[cmd] = discord.Embed(title=cmd_data["title"], color=cmd_data["color"], description=cmd_data["description"])
    
    command_list_embed.add_field(name="u200B", value="u200B")
    command_list_embed.add_field(name="About nfc-info-bot", value="Idea and prototype by @Sm0keWag0n, but @Carson made the NodeJS actually good. Then it got re-written in Python. ¯\_(ツ)_/¯", inline=False)
    command_list_embed.add_field(name="Contribute", value="This info is community-driven. If you have ideas or information to add/correct, please visit the [GitHub Repo](https://github.com/mikedalton/nfc-info-bot) and submit Issues, or fork/pull request.", inline=False)

update_commands()

print(command_embeds)

client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    if message.content.startswith("^py-info-bot"):
        await message.channel.send(embed=command_list_embed)

client.run(TOKEN)