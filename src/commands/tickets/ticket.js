import { SlashCommandBuilder } from "@discordjs/builders";
import Guild from "../../lib/models/Guild.js";

const data = new SlashCommandBuilder()
  .setName("ticket")
  .setDescription("Ticket commands")
  .addSubcommand((subcommand) =>
    subcommand
      .setName("channel")
      .setDescription("Set the ticket channel")
      .addChannelOption((option) =>
        option
          .setName("channel")
          .setDescription("The channel to set as the ticket channel")
          .setRequired(true),
      ),
  );

const execute = async function (interaction) {
  const subCommand = interaction.options.getSubcommand();

  if (subCommand === "channel") {
    const channel = interaction.options.getChannel("channel");

    if (!interaction.member.permissions.has("MANAGE_CHANNELS")) {
      return interaction.reply({
        content: "You do not have permission to use this command",
        ephemeral: true,
      });
    }

    const guild = await Guild.findOne({ id: interaction.guild.id });

    if (!guild) {
      await Guild.create({
        id: interaction.guild.id,
        ticketChannel: channel.id,
      });
    } else {
      guild.ticketChannel = channel.id;
      await guild.save();
    }

    await interaction.reply({
      content: `Ticket channel set to <#${channel.id}>`,
      ephemeral: true,
    });
  }
};

export default { data, execute };
