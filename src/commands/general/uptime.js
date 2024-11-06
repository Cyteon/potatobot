import { SlashCommandBuilder } from "@discordjs/builders";

const data = new SlashCommandBuilder()
  .setName("uptime")
  .setDescription("Get the uptime of the bot")
  .setIntegrationTypes(0, 1)
  .setContexts(0, 1, 2);

const execute = async function (interaction) {
  const uptime = process.uptime();
  const days = Math.floor(uptime / 86400);
  const hours = Math.floor(uptime / 3600) % 24;
  const minutes = Math.floor(uptime / 60) % 60;
  const seconds = Math.floor(uptime) % 60;

  await interaction.reply(
    `🕒 Uptime: ${days}d ${hours}h ${minutes}m ${seconds}s`,
  );
};

export default { data, execute };
