# bot.py
import os, re, discord, requests, threading, sqlite3, datetime, json, yaml
from discord import Option
from discord.ui import View, Select, Button
from discord import SelectOption, ButtonStyle, Interaction

from thefuzz import fuzz
from prettytable import PrettyTable

if os.getenv('LOCAL_TESTING') == 'True':
    import dotenv
    dotenv.load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
COMMAND_URL = os.getenv('COMMAND_URL')
ADMIN_USERS = json.loads(os.getenv('ADMIN_USER'))
LOG_CHANNEL = os.getenv('LOG_CHANNEL')
try:
    GUILD_IDS = json.loads(os.getenv('GUILD_IDS', '[]'))
    if not isinstance(GUILD_IDS, list):
        print("GUILD_IDS env var is not a list; defaulting to empty (global registration).")
        GUILD_IDS = []
except Exception as e:
    print(f"Failed to parse GUILD_IDS: {e}")
    GUILD_IDS = []
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
    global command_list, command_data, command_embeds, dm_embeds, command_list_embed

    if os.getenv('LOCAL_TESTING') == 'True':
        print("Loading commands from local YAML files")
        with open("commands.yaml", "r") as f:
            command_list = yaml.safe_load(f)
        for cmd in command_list:
            with open("commands/" + cmd + ".yaml", "r") as f:
                command_detail = yaml.safe_load(f)
            command_data[cmd] = command_detail
    else:
        print("Loading commands from remote YAML")
        with requests.get(COMMAND_URL + "commands.yaml") as response:
            command_list = yaml.safe_load(response.text)
        for cmd in command_list:
            with requests.get(COMMAND_URL + "commands/" + str(cmd) + ".yaml") as response:
                command_detail = yaml.safe_load(response.text)
            command_data[cmd] = command_detail

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

# Switch to discord.Bot (inherits from Client) to allow slash command registration while preserving existing functionality
client = discord.Bot(intents=intents)

# Load chassis list for slash command filtering
chassis_list = []
try:
    with open("chassis.yaml", "r") as f:
        chassis_list = yaml.safe_load(f) or []
except Exception as e:
    print(f"Failed to load chassis.yaml: {e}")

def _build_all_commands_embed():
    """Build an embed listing all commands with their title (context) dynamically.
    This differs from the existing command_list_embed (which shows 'info').
    """
    embed = discord.Embed(title="Available Commands", color=0x0099ff)
    for cmd, data in command_data.items():
        title = data.get("title", data.get("info", ""))
        embed.add_field(name=cmd, value=title if title else "", inline=False)
    return embed

def _filter_fields_by_chassis(cmd: str, chassis: str):
    """Return list of fields for a command filtered by chassis selection.
    chassis == 'ALL' returns all fields. If a field lacks a 'chassis' key it is treated as ALL.
    """
    data = command_data.get(cmd)
    if not data:
        return []
    selected = chassis or 'ALL'
    result = []
    for field in data.get("fields", []):
        field_chassis = field.get("chassis")
        if not field_chassis or 'ALL' in field_chassis or selected == 'ALL' or selected in field_chassis:
            result.append(field)
    return result

async def _command_autocomplete(ctx):
    """Autocomplete handler for the 'command' option."""
    entered = (ctx.value or '').lower()
    # limit to 25 per Discord API
    return [cmd for cmd in command_data.keys() if cmd.lower().startswith(entered)][:25]

async def _chassis_autocomplete(ctx):
    """Autocomplete handler for the 'chassis' option based on selected command's field chassis lists."""
    # Determine which command (if any) the user has already selected
    selected_command = ctx.options.get('command')
    suggestions = set()
    if selected_command and selected_command in command_data:
        for field in command_data[selected_command].get("fields", []):
            field_chassis = field.get("chassis") or ['ALL']
            for c in field_chassis:
                if c != 'ALL':
                    suggestions.add(c)
    else:
        # fallback to global chassis list if no command chosen yet
        suggestions.update([c for c in chassis_list if c != 'ALL'])
    # Always allow ALL as an implicit choice
    suggestions = list(suggestions)
    suggestions.sort()
    entered = (ctx.value or '').lower()
    filtered = [c for c in suggestions if c.lower().startswith(entered)]
    # Provide at least 'ALL' if nothing matches
    if not filtered:
        filtered = []
    # Prepend ALL (display) if matches prefix or if no entry typed
    if 'all'.startswith(entered) or entered == '':
        filtered.insert(0, 'ALL')
    return filtered[:25]

# ---------------- UI Kit (Graphical) Implementation ---------------- #

class CommandSelect(Select):
    def __init__(self, parent_view: 'InfoBotView'):
        options = []
        for cmd, data in command_data.items():
            title = data.get('title') or data.get('info') or ''
            if title and len(title) > 95:
                title_trunc = title[:92] + '...'
            else:
                title_trunc = title
            options.append(SelectOption(label=cmd, description=title_trunc or None))
        super().__init__(placeholder="Select a command", min_values=1, max_values=1, options=options)
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        self.parent_view.selected_command = self.values[0]
        # Clear chassis selection when command changes
        self.parent_view.selected_chassis = None
        self.parent_view.rebuild_chassis_select()
        # Enable Go button now that a command is selected
        if self.parent_view.go_button:
            self.parent_view.go_button.disabled = False
            self.parent_view.show_embed = False
        await self.parent_view.refresh(interaction)

class ChassisSelect(Select):
    def __init__(self, parent_view: 'InfoBotView', command: str | None, current: str | None):
        # Only show when a valid command is chosen. Allow no selection (min_values=0) -> blank means ALL.
        # The parent view already checks for specific chassis before instantiating this select, so no need to re-check here.
        if not command or command not in command_data:
            options = [SelectOption(label="Select command first", value="_placeholder", description="Choose a command", default=True)]
            super().__init__(placeholder="Select chassis (optional)", min_values=0, max_values=1, options=options, disabled=True)
            self.parent_view = parent_view
            return
        chassis_set = set()
        for field in command_data[command].get('fields', []):
            ch = field.get('chassis') or ['ALL']
            for c in ch:
                if c != 'ALL':
                    chassis_set.add(c)
        options = []
        for c in sorted(chassis_set):
            options.append(SelectOption(label=c, value=c, default=(current == c)))
        # If somehow instantiated with empty set, disable (should be prevented by caller)
        disabled = len(options) == 0
        super().__init__(placeholder="Chassis filter (optional)", min_values=0, max_values=1, options=options, disabled=disabled)
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        # values empty -> treat as ALL (None internally)
        if self.values:
            val = self.values[0]
            self.parent_view.selected_chassis = None if val == 'ALL' else val
        else:
            self.parent_view.selected_chassis = None
        # Changing selection invalidates previously shown embed until Go clicked again
        self.parent_view.show_embed = False
        await self.parent_view.refresh(interaction)

class ResetButton(Button):
    def __init__(self, parent_view: 'InfoBotView'):
        super().__init__(label="Reset", style=ButtonStyle.secondary)
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        self.parent_view.selected_command = None
        self.parent_view.selected_chassis = None
        self.parent_view.show_embed = False
        if self.parent_view.go_button:
            self.parent_view.go_button.disabled = True
        self.parent_view.rebuild_all_selects()
        await self.parent_view.refresh(interaction)

class GoButton(Button):
    def __init__(self, parent_view: 'InfoBotView'):
        super().__init__(label="Go", style=ButtonStyle.primary, disabled=True)
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        if not self.parent_view.selected_command:
            await interaction.response.edit_message(content="Select a command first.", view=self.parent_view, embed=None)
            return
        self.parent_view.show_embed = True
        await self.parent_view.refresh(interaction)

class CloseButton(Button):
    def __init__(self, parent_view: 'InfoBotView'):
        super().__init__(label="Close", style=ButtonStyle.danger)
        self.parent_view = parent_view

    async def callback(self, interaction: Interaction):
        # Disable all interactive components and remove view
        for child in self.parent_view.children:
            if hasattr(child, 'disabled'):
                child.disabled = True
        await interaction.response.edit_message(content="Interaction closed.", embed=None, view=None)

class InfoBotView(View):
    def __init__(self):
        super().__init__(timeout=300)
        self.selected_command: str | None = None
        self.selected_chassis: str | None = None
        self.command_select: CommandSelect | None = None
        self.chassis_select: ChassisSelect | None = None
        self.reset_button = ResetButton(self)
        self.go_button = GoButton(self)
        self.close_button = CloseButton(self)
        self.show_embed = False
        self.rebuild_all_selects()
        self.add_item(self.reset_button)
        self.add_item(self.go_button)
        self.add_item(self.close_button)

    def rebuild_all_selects(self):
        if self.command_select:
            self.remove_item(self.command_select)
        if self.chassis_select:
            self.remove_item(self.chassis_select)
        self.command_select = CommandSelect(self)
        self.add_item(self.command_select)
        # Only add chassis select when a command has been chosen AND there are specific chassis
        if self.selected_command:
            specific = self._command_has_specific_chassis(self.selected_command)
            if specific:
                self.chassis_select = ChassisSelect(self, self.selected_command, self.selected_chassis)
                self.add_item(self.chassis_select)
            else:
                self.chassis_select = None
        else:
            self.chassis_select = None

    def rebuild_chassis_select(self):
        if self.chassis_select:
            self.remove_item(self.chassis_select)
        if self.selected_command and self._command_has_specific_chassis(self.selected_command):
            self.chassis_select = ChassisSelect(self, self.selected_command, self.selected_chassis)
            self.add_item(self.chassis_select)
        else:
            self.chassis_select = None

    def build_embed(self) -> discord.Embed | None:
        if not self.show_embed or not self.selected_command:
            return None
        if self.selected_command not in command_data:
            return discord.Embed(title="Unknown command", description="Data not found.", color=0xff0000)
        data = command_data[self.selected_command]
        # If there are no specific chassis for this command, force ALL
        if not self._command_has_specific_chassis(self.selected_command):
            chassis_effective = 'ALL'
        else:
            chassis_effective = self.selected_chassis or 'ALL'
        embed = discord.Embed(title=data.get("title", self.selected_command), description=data.get("description", ''), color=0x0099ff)
        fields = _filter_fields_by_chassis(self.selected_command, chassis_effective)
        for field in fields:
            embed.add_field(name=field.get("name", ""), value=field.get("value", ""), inline=field.get("inline", False))
        embed.set_footer(text=f"Chassis: {chassis_effective}")
        return embed
    def _command_has_specific_chassis(self, command: str) -> bool:
        data = command_data.get(command)
        if not data:
            return False
        for field in data.get('fields', []):
            ch = field.get('chassis') or ['ALL']
            if any(c != 'ALL' for c in ch):
                return True
        return False

    async def refresh(self, interaction: Interaction):
        embed = self.build_embed()
        content = None
        if embed is None:
            # Formulate guidance message based on current state
            if not self.selected_command:
                content = "Select a command, optionally choose a chassis (or leave blank for ALL), then press Go."
            else:
                content = "Optionally select a chassis (blank = ALL) and press Go to display the data."
        await interaction.response.edit_message(content=content, embed=embed, view=self)

    async def on_timeout(self):
        for child in self.children:
            if hasattr(child, 'disabled'):
                child.disabled = True
        # Cannot edit without a message ref; rely on user invoking again.
        # If needed, this could be extended by storing message reference on send.
        pass

@client.slash_command(name="infobot", description="Query NFC info bot data", guild_ids=GUILD_IDS if GUILD_IDS else None)
async def infobot(
    ctx: discord.ApplicationContext,
    command: str = Option(str, "Command name", required=False, autocomplete=_command_autocomplete),
    chassis: str = Option(str, "Chassis filter", required=False, autocomplete=_chassis_autocomplete)
):
    """Slash command interface for info bot. Does not alter existing prefix behavior."""
    try:
        if not command:
            embed = _build_all_commands_embed()
            await ctx.respond(embed=embed, ephemeral=False)
            return
        if command not in command_data:
            await ctx.respond(f"Unknown command '{command}'.", ephemeral=True)
            return
        data = command_data[command]
        embed = discord.Embed(title=data.get("title", command), description=data.get("description", ''), color=0x0099ff)
        selected_chassis = chassis or 'ALL'
        fields = _filter_fields_by_chassis(command, selected_chassis)
        for field in fields:
            embed.add_field(name=field.get("name", ""), value=field.get("value", ""), inline=field.get("inline", False))
        # Removed DM-related note for slash command per updated requirements.
        # If chassis filtered (not ALL) add footer
        if selected_chassis != 'ALL':
            embed.set_footer(text=f"Filtered by chassis: {selected_chassis}")
        await ctx.respond(embed=embed, ephemeral=False)
    except Exception as e:
        await ctx.respond(f"Error building embed: {e}", ephemeral=True)

@client.slash_command(name="infobotui", description="Interactive UI for browsing NFC info bot data", guild_ids=GUILD_IDS if GUILD_IDS else None)
async def infobotui(ctx: discord.ApplicationContext):
    """Launch interactive command/chassis browser using UI components. No embed until both selections made."""
    view = InfoBotView()
    await ctx.respond(content="Select a command and chassis to display data.", view=view, ephemeral=False)

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
