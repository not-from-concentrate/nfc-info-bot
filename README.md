# nfc-info-bot

## About

The nfc-info-bot exists to assist with providing fast and standardized answers to many of the most common questions asked on the NFC Discord server. The goal is for this information to be community-driven, but still moderated. If you would like to contribute to the project, please feel free to fork it, or open issues (please use the `new command`, `new info`, or `incorrect info` labels for most submissions, as appropriate). If you would like more direct involvement, message @Sm0keWag0n on the NFC Discord server to request access.

## Command Data

Command data is now stored in YAML format for improved readability and maintainability.

- The main command index is in [`commands.yaml`](commands.yaml), which lists all available command names (one per line).
- Each command has its own YAML file in the [`commands/`](commands/) directory (e.g., `brickless.yaml`, `gpu.yaml`), containing all metadata and details for that command.

### Example: Main Index (`commands.yaml`)
```yaml
- "180"
- brickless
- gpu
- psu
# ...other command names...
```

### Example: Individual Command File (`commands/brickless.yaml`)
```yaml
info: Brickless configurations
color: "#0099ff"
title: Brickless Fitment Info
description: "\"Brickless\" is a configuration where the..."
dm: false
fields:
  - name: Standard Layout
    value: The most common brickless configuration is...
    inline: false
```

| Section         | Detail                                                                 |
|-----------------|-----------------------------------------------------------------------|
| `info`          | Short description for command list                                    |
| `color`         | Color for MessageEmbed object (usually "#0099ff")                     |
| `title`         | Header for MessageEmbed                                               |
| `description`   | Main block of text in the MessageEmbed                                |
| `dm`            | Set to true if the content is long enough to cause channel congestion |
| `fields`        | List of subsections for the command                                   |
| `fields.name`   | Header for subsection                                                 |
| `fields.value`  | Text content for subsection                                           |
| `fields.inline` | false for large blocks, true for short (one-line) data                |

Commands should be kept alphabetized in the index for convenience, but this is not enforced automatically.

## Bot Command Updates

The bot will automatically refresh its list of commands from the repo hourly at the top of the hour, so once changes have been approved and merged into the master branch, they will be visible in the bot within an hour. If you believe that the change is important enough to warrant immediate update, please ping @Sm0keWag0n on the NFC Discord server.

## Environment Variables

| Variable | Description |
|-|-|
| BOT_TOKEN | Discord bot token used for authentication |
| COMMAND_URL | URL to the repository raw content base |
| ADMIN_USER | ID of discord user who can run restricted commands |
| LOG_CHANNEL | ID of channel to log information to |
