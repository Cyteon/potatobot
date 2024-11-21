import { SlashCommandSubcommandBuilder } from "discord.js";

const data = new SlashCommandSubcommandBuilder()
    .setName("pause")
    .setDescription("Pause the player");

const execute = async function (interaction) {
    const player = interaction.client.kazagumo.getPlayer(interaction.guildId);

    if (!player) {
      return await interaction.reply("I'm not playing anything.");
    }

    if (player.paused) {
      return await interaction.reply("Player is already paused.");
    }

    await player.pause(true);

    await interaction.reply("Player paused.");
}

export default { data, execute };