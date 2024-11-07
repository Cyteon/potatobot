import { SlashCommandBuilder } from "@discordjs/builders";

const data = new SlashCommandBuilder()
  .setName("ping")
  .setDescription("Gets the current ping of the bot")
  .setIntegrationTypes(0, 1)
  .setContexts(0, 1, 2);

const execute = async function (interaction) {
  await interaction.reply(`🏓 Pong! ${interaction.client.ws.ping}ms`);
};

export default { data, execute };
