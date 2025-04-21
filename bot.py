# bot.py
import os, re, discord, requests, threading, sqlite3, datetime, json

from thefuzz import fuzz
from prettytable import PrettyTable

if os.getenv('LOCAL_TESTING') == 'True':
    import dotenv
    dotenv.load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
COMMAND_URL = os.getenv('COMMAND_URL')
ADMIN_USERS = json.loads(os.getenv('ADMIN_USER'))
LOG_CHANNEL = os.getenv('LOG_CHANNEL')
LINK_PATTERN = r'(?:https?:\/\/)(?:[^@\n]+@)?([^:\/\n\s?]+)'
REAL_GIFT_DOMAIN = 'discord.gift'
MIN_RATIO = 90

# Init variables
command_data = {}
command_embeds = {}
dm_embeds = {}
command_list_embed = {}
stats_db_file = None
if os.getenv('LOCAL_TESTING') == 'True':
    stats_db_file = "stats.db"
else:
    stats_db_file = "/db/stats.db"
conn = None

try:
    conn = sqlite3.connect(stats_db_file)
    cursor = conn.cursor()
    print("Database loaded")
except sqlite3.Error as e:
    print(e)
        
# Set up stats database
def database_setup():
    schema_version = 0
    cursor.row_factory = lambda cursor, row: row[0]
    # determine schema version
    table_list = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    if 'stats' in table_list:
        schema_version = 1
    if 'metadata' in table_list:
        schema_version = cursor.execute("SELECT schema_version FROM metadata").fetchone()
    # create tables
    if schema_version < 1:
        print("Upgrading database to schema version 1")
        conn.execute("CREATE TABLE stats ( \
                    command TEXT PRIMARY KEY, \
                    invocation_count INTEGER, \
                    last_invocation TEXT \
                    );")
        conn.commit()
    if schema_version < 2:
        print("Upgrading database to schema version 2")
        print("Creating metadata table")
        conn.execute("CREATE TABLE IF NOT EXISTS metadata ( \
                    setting_id INTEGER PRIMARY KEY, \
                    schema_version INTEGER NOT NULL \
                    );")
        conn.commit()
        print("Inserting initial metadata row")
        conn.execute("INSERT INTO metadata VALUES (?,?)", [1, 2])
        conn.commit()
        print("Creating bot_message_log table")
        conn.execute("CREATE TABLE IF NOT EXISTS bot_message_log ( \
                    message_id INTEGER PRIMARY KEY, \
                    guild_id INTEGER NOT NULL, \
                    channel_id INTEGER NOT NULL, \
                    Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, \
                    Source STRING NOT NULL \
                    );")
        conn.commit()
    print("Database verified at schema version {}".format(schema_version))

def get_stats():
    stats = conn.execute("SELECT * FROM stats").fetchall()

    text_table = PrettyTable()
    
    text_table.field_names = ["Command", "Invocation Count", "Last Invocation"]
    text_table.align["Command"] = "l"
    text_table.align["Invocation Count"] = "r"
    text_table.align["Last Invocation"] = "l"

    for row in stats:
        text_table.add_row([row[0], row[1], row[2]])

    return text_table.get_string(title="Current nfc-info-bot stats")

# Set up the commands JSON file pull and parse
def update_commands():
    global command_data, command_embeds, dm_embeds, command_list_embed

    if os.getenv('LOCAL_TESTING') == 'True':
        with open("commands.json", "r") as f:
            command_data = json.load(f)
    else:
        with requests.get(COMMAND_URL) as response:
            command_data = response.json()

    command_list_embed = discord.Embed(title="Command List", color=0x0099ff)
    for cmd in command_data:
        cmd_data = command_data[cmd]
        if cmd_data["dm"]:
            command_list_embed.add_field(name="!"+cmd+" [@username]", value=cmd_data["info"], inline=True)
        else:
            command_list_embed.add_field(name="!"+cmd, value=cmd_data["info"], inline=True)
        
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
    command_list_embed.add_field(name="About nfc-info-bot", value="Idea and prototype by @Sm0keWag0n, but @Carson made the NodeJS actually good. Then it got re-written in Python.", inline=False)
    command_list_embed.add_field(name="Contribute", value="This info is community-driven. If you have ideas or information to add/correct, please visit the [GitHub repo](https://github.com/not-from-concentrate/nfc-info-bot) and submit Issues, or fork/pull request.", inline=False)

    print(command_data.keys())

    # Quick and dirty threading hourly loop
    threading.Timer(3600.00, update_commands).start()

database_setup()

update_commands()

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

async def check_for_bad_links(message, domains):
    log_channel = client.get_channel(int(LOG_CHANNEL))
    for domain in domains:
        ratio = fuzz.ratio(REAL_GIFT_DOMAIN, domain)
        if ratio >= MIN_RATIO and ratio < 100:
            await message.delete()
            await log_channel.send(f'Deleted message from <@{message.author.id}> for suspicious link')
            break

async def handle_command(message):
    if message.content.startswith("!"):
        if message.content.lower() == "!info-bot":
            response = await message.channel.send(embed=command_list_embed)
        elif message.content.lower() == "!update-commands":
            print("Update attempt: " + str(message.author.id))
            if message.author.id in ADMIN_USERS:
                update_commands()
                await message.channel.send("Commands updated")
            else:
                await message.channel.send("Not authorized")
        elif message.content.lower() == "!info-bot-stats":
            print("Stats attempt: " + str(message.author.id))
            if message.author.id in ADMIN_USERS:
                await message.channel.send("```" + get_stats() + "```")
            else:
                await message.channel.send("Not authorized")
        else:
            if len(message.mentions) > 0:
                user = message.mentions[0]
            else:
                user = message.author
            command = message.content.split()[0].lower().lstrip("!")

            if command in command_data:
                response = await message.channel.send(embed=command_embeds[command])
                if command_data[command]["dm"]:
                    await user.send(embed=dm_embeds[command])
                print("Logging command")
                cursor = conn.cursor()
                # log stats
                cursor.execute("SELECT * from stats WHERE command=?", ["!"+command])
                command_row = cursor.fetchall()
                if len(command_row) == 0:
                    conn.execute("INSERT INTO stats VALUES (?,?,?)", ["!"+command, 1, datetime.datetime.utcnow()])
                    conn.commit()
                elif len(command_row) == 1:
                    conn.execute("UPDATE stats SET invocation_count=?, last_invocation=? WHERE command = ?", [command_row[0][1]+1, datetime.datetime.utcnow(), "!"+command])
                    conn.commit()
                else:
                    print("Database error: too many matching rows")
                # log messages
                conn.execute("INSERT INTO bot_message_log (message_id, guild_id, channel_id, Source) VALUES (?, ?, ?, ?)", [message.id, message.channel.guild.id, message.channel.id, "User"])
                conn.commit()
                conn.execute("INSERT INTO bot_message_log (message_id, guild_id, channel_id, Source) VALUES (?, ?, ?, ?)", [response.id, response.channel.guild.id, response.channel.id, "Bot"])
                conn.commit()

@client.event
async def on_message(message):
    domains = re.findall(LINK_PATTERN, message.content)
    if domains:
        await check_for_bad_links(message, domains)
    elif message.content.startswith("!"):
        await handle_command(message)

client.run(TOKEN)
