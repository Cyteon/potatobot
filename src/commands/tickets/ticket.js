import { SlashCommandBuilder } from "@discordjs/builders";
import Guild from "../../lib/models/Guild.js";
import { PermissionFlagsBits } from "discord.js";

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
  )
  .addSubcommand((subcommand) =>
    subcommand
      .setName("logs")
      .setDescription("Set the ticket logs channel")
      .addChannelOption((option) =>
        option
          .setName("channel")
          .setDescription(
            "The channel to set (only staff should be able to see this channel)",
          )
          .setRequired(true),
      ),
  )
  .addSubcommand((subcommand) =>
    subcommand
      .setName("add")
      .setDescription("Add a user to a ticket")
      .addUserOption((option) =>
        option
          .setName("user")
          .setDescription("The user to add to the ticket")
          .setRequired(true),
      ),
  )
  .addSubcommand((subcommand) =>
    subcommand
      .setName("remove")
      .setDescription("Remove a user from a ticket")
      .addUserOption((option) =>
        option
          .setName("user")
          .setDescription("The user to remove from the ticket")
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
  } else if (subCommand === "logs") {
    const channel = interaction.options.getChannel("channel");

    if (
      !interaction.member.permissions.has(PermissionFlagsBits.ManageChannels)
    ) {
      return interaction.reply({
        content: "You do not have permission to use this command",
        ephemeral: true,
      });
    }

    const guild = await Guild.findOne({ id: interaction.guild.id });

    if (!guild) {
      await Guild.create({
        id: interaction.guild.id,
        ticketLogChannel: channel.id,
      });
    }

    guild.ticketLogChannel = channel.id;
    await guild.save();

    await interaction.reply({
      content: `Ticket logs channel set to <#${channel.id}>`,
      ephemeral: true,
    });
  } else if (subCommand === "add") {
    const user = interaction.options.getUser("user");

    if (
      !interaction.member.permissions.has(PermissionFlagsBits.ManageChannels)
    ) {
      return interaction.reply({
        content: "You do not have permission to use this command",
        ephemeral: true,
      });
    }

    await interaction.channel.members.add(user);

    await interaction.reply({
      content: `User <@${user.id}> added to ticket`,
    });
  } else if (subCommand === "remove") {
    const user = interaction.options.getUser("user");

    if (!interaction.member.permissions.has("MANAGE_CHANNELS")) {
      return interaction.reply({
        content: "You do not have permission to use this command",
        ephemeral: true,
      });
    }

    await interaction.channel.members.remove(user);

    await interaction.reply({
      content: `User **${user.tag}** removed from ticket`,
    });
  }
};

export default { data, execute };
