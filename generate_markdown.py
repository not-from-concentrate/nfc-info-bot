import json

# Load the JSON data from commands.json
with open('commands.json', 'r') as json_file:
    data = json.load(json_file)

# Open the output markdown file
with open('info-bot-commands.md', 'w') as md_file:
    for key, value in data.items():
        title = value.get('title', '')
        description = value.get('description', '')
        fields = value.get('fields', [])

        # Write the section heading
        md_file.write(f'# {title}\n\n')

        # Write the description
        if description:
            md_file.write(f'{description}\n\n')

        # Write the fields
        for field in fields:
            name = field.get('name', '')
            field_value = field.get('value', '')
            md_file.write(f'## {name}\n\n')
            md_file.write(f'{field_value}\n\n')
