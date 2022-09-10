const { SlashCommandBuilder, Routes } = require('discord.js');
const { REST } = require('@discordjs/rest');
const fs = require('fs');
const clientId = process.env.CLIENT_ID;
const guildId = process.env.GUILD_ID;
const token = process.env.BOT_TOKEN;

var content;
fs.readFile('commands.json', 'utf8', function (err, data) {
    if (err) {
        console.log(err);
        process.exit(1);
    }
    content = data.replace(/"!/g, '"');
});

const commands = JSON.parse(content);

/*
const commands = [
	new SlashCommandBuilder().setName('ping').setDescription('Replies with pong!'),
	new SlashCommandBuilder().setName('server').setDescription('Replies with server info!'),
	new SlashCommandBuilder().setName('user').setDescription('Replies with user info!'),
]
	.map(command => command.toJSON());
*/
const rest = new REST({ version: '10' }).setToken(token);

rest.put(Routes.applicationGuildCommands(clientId, guildId), { body: commands })
	.then((data) => console.log(`Successfully registered ${data.length} application commands.`))
	.catch(console.error);
