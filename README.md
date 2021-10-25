# nfc-info-bot

## About

The nfc-info-bot exists to assist with providing fast and standardized answers to many of the most common questions asked on the NFC Discord server. The goal is for this information to be community-driven, but still moderated. If you would like to contribute to the project, please feel free to fork it, or open issues (please use the `new command`, `new info`, or `incorrect info` labels for most submissions, as appropriate). If you would like more direct involvement, message @Sm0keWag0n on the NFC Discord server to request access.

## Command Data

Data for the commands is stored in JSON format, in the [commands.json](commands.json) file. Most of the data is what is required for an Embed object, but some fields have been added. Keeping the commands alphabetized is preferred, although not required and there is no linting to enforce such.

Example:
```
    "!brickless": {
        "info": "Brickless configurations",
        "color": "#0099ff",
        "title": "Brickless Fitment Info",
        "description": "\"Brickless\" is a configuration where the...",
        "dm": false,
        "fields": [
            {
                "name": "Standard Layout",
                "value": "The most common brickless configuration is....",
                "inline": false
            }
        ]
    }
```

|Section   |Detail   |
|---|---|
|"!brickless"   |Command name   |
|"info"   |Short name for for command list   |
|"color"   |Color for MessageEmbed object (generally leave this set to "#0099ff")  |
|"title"   |Header for MessageEmbed   |
|"description"   |Main block of text in the MessageEmbed   |
|"dm"   |Set to true if the content is long enough to cause channel congestion issues   |
|"fields"   |Add a field entry for each subsection, and try to keep subsection content short   |
|"fields"->"name"   |Header for subsection   |
|"fields"->"value"   |Text content for subsection   |
|"fields"->"inline"   |false for large content blocks, true for very small (one-line) data   |

## Bot Command Updates

The bot will automatically refresh its list of commands from the repo hourly at the top of the hour, so once changes have been approved and merged into the master branch, they will be visible in the bot within an hour. If you believe that the change is important enough to warrant immediate update, please ping @Sm0keWag0n on the NFC Discord server.

## Environment Variables

| Variable | Description |
|-|-|
| BOT_TOKEN | Discord bot token used for authentication |
| COMMAND_URL | URL to commands.json for command data |
| ADMIN_USER | ID of discord user who can run restricted commands |
| LOG_CHANNEL | ID of channel to log information to |
