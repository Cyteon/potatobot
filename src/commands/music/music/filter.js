import { SlashCommandSubcommandGroupBuilder } from "discord.js";

const data = new SlashCommandSubcommandGroupBuilder()
    .setName("filter")
    .setDescription("Set filters for the player")
    .addSubcommand((subcommand) =>
        subcommand
            .setName("speed")
            .setDescription("Set the speed of the player")
            .addNumberOption((option) =>
                option
                    .setName("speed")
                    .setDescription("The speed to set")
                    .setRequired(true),
            ),
    )
    .addSubcommand((subcommand) =>
        subcommand
            .setName("pitch")
            .setDescription("Set the pitch of the player")
            .addNumberOption((option) =>
                option
                    .setName("pitch")
                    .setDescription("The pitch to set")
                    .setRequired(true),
            ),
    );

const execute = async function (interaction) {
    const filterSubcommand = interaction.options.getSubcommand();

    const player = interaction.client.kazagumo.getPlayer(interaction.guildId);

    if (!player) {
      return await interaction.reply("I'm not playing anything.");
    }

    if (filterSubcommand == "speed") {
      const speed = interaction.options.getNumber("speed");

      await player.setFilters({
        speed: speed,
      });

      await interaction.reply(`Speed set to ${speed}.`);
    } else if (filterSubcommand == "pitch") {
      const pitch = interaction.options.getNumber("pitch");

      await player.setFilters({
        pitch: pitch,
      });

      await interaction.reply(`Pitch set to ${pitch}.`);
    }
}

export default { data, execute };