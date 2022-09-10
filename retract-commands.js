const { Routes } = require('discord.js');
const { REST } = require('@discordjs/rest');
const clientId = process.env.CLIENT_ID;
const guildId = process.env.GUILD_ID;
const token = process.env.BOT_TOKEN;

const rest = new REST({ version: '10' }).setToken(token);

rest.put(Routes.applicationGuildCommands(clientId, guildId), { body: [] })
	.then(() => console.log('Successfully retracted all guild commands.'))
	.catch(console.error);