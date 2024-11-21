import { SlashCommandSubcommandBuilder } from "discord.js";

const data = new SlashCommandSubcommandBuilder()
    .setName("volume")
    .setDescription("Change the volume of the player")
    .addIntegerOption((option) =>
        option
            .setName("volume")
            .setDescription("The volume to set")
            .setRequired(true),
    );

const execute = async function (interaction) {
    const volume = interaction.options.getInteger("volume");

    const player = interaction.client.kazagumo.getPlayer(interaction.guildId);

    if (!player) {
      return await interaction.reply("I'm not playing anything.");
    }

    await player.setVolume(volume);

    await interaction.reply(`Volume set to ${volume}.`);
}

export default { data, execute };