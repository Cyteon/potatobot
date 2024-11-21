import { SlashCommandSubcommandBuilder } from "discord.js";

const data = new SlashCommandSubcommandBuilder()
    .setName("leave")
    .setDescription("Leave the voice channel");

const execute = async function (interaction) {
    const player = interaction.client.kazagumo.getPlayer(interaction.guildId);

    if (!player) {
      return await interaction.reply("I'm not playing anything.");
    }

    await player.destroy();

    await interaction.reply("Left the voice channel.");
}

export default { data, execute };