# bot.py
import os, discord, urllib.request, json
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
COMMAND_URL = os.getenv('COMMAND_URL')
ADMIN_USER = os.getenv('ADMIN_USER')

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
        
        command_embeds[cmd] = discord.Embed(title=cmd_data["title"], color=0x0099ff, description=cmd_data["description"])
        dm_embeds[cmd] = discord.Embed(title=cmd_data["title"], color=0x0099ff, description=cmd_data["description"])

        for field in cmd_data["fields"]:
            if cmd_data["dm"]:
                dm_embeds[cmd].add_field(name=field["name"], value=field["value"], inline=field["inline"])
            else: 
                command_embeds[cmd].add_field(name=field["name"], value=field["value"], inline=field["inline"])

        if cmd_data["dm"]:
            command_embeds[cmd].add_field(name="Notes", value="There is a *lot* of data on this topic. Please check the DM you were just sent.", inline=False)
    
    command_list_embed.add_field(name="\u200B", value="\u200B")
    command_list_embed.add_field(name="About nfc-info-bot", value="Idea and prototype by @Sm0keWag0n, but @Carson made the NodeJS actually good. Then it got re-written in Python. ¯\_(ツ)_/¯", inline=False)
    command_list_embed.add_field(name="Contribute", value="This info is community-driven. If you have ideas or information to add/correct, please visit the [GitHub Repo](https://github.com/mikedalton/nfc-info-bot) and submit Issues, or fork/pull request.", inline=False)

    print(command_data.keys())

update_commands()

client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    if message.content.startswith("!"):
        if message.content == "!info-bot":
            await message.channel.send(embed=command_list_embed)
        elif message.content == "!update-commands":
            print("Update attempt: " + str(message.author.id))
            if message.author.id == int(ADMIN_USER):
                update_commands()
                await message.channel.send("Commands updated")
        else:
            if len(message.mentions) > 0:
                user = message.mentions[0]
            else:
                user = message.author
            command = message.content.split()[0]

            if command in command_data:
                if command_data[command]["dm"]:
                    await message.channel.send(embed=command_embeds[command])
                    await user.send(embed=dm_embeds[command])
                else:
                    await message.channel.send(embed=command_embeds[command])

client.run(TOKEN)