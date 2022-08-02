import json

command_data = {}
command_embeds = {}

f = open('commands.json')

command_data = json.load(f)

print("Command data is valid JSON.")

for cmd in command_data:
    cmd_data = command_data[cmd]
    for field in cmd_data["fields"]:
        if len(field["value"]) > 1024:
            raise Exception('The length of the value of field "{}" in command "{}" exceeds 1,024 characters.'.format(field["name"], cmd))