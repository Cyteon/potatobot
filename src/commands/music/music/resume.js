import { SlashCommandSubcommandBuilder } from "discord.js";

const data = new SlashCommandSubcommandBuilder()
    .setName("resume")
    .setDescription("Resume the player");
  
const execute = async function (interaction) {
  const player = interaction.client.kazagumo.getPlayer(interaction.guildId);

  if (!player) {
    return await interaction.reply("I'm not playing anything.");
  }

  if (!player.paused) {
    return await interaction.reply("Player is already playing.");
  }

  await player.pause(false);

  await interaction.reply("Player resumed.");
}

export default { data, execute };