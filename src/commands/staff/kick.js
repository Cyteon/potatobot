import { SlashCommandBuilder } from "@discordjs/builders";
import { PermissionFlagsBits } from "discord.js";
import Guild from "../../lib/models/Guild.js";

const data = new SlashCommandBuilder()
  .setName("kick")
  .setDescription("Kick a user")
  .addUserOption((option) =>
    option.setName("user").setDescription("The user to kick").setRequired(true),
  )
  .addStringOption((option) =>
    option.setName("reason").setDescription("The reason for kicking the user"),
  )
  .setDefaultMemberPermissions(PermissionFlagsBits.KickMembers);

const execute = async function (interaction) {
  const user = interaction.options.getUser("user");
  const reason =
    interaction.options.getString("reason") || "No reason provided";

  const member = interaction.guild.members.cache.get(user.id);

  if (!member) {
    const embed = {
      title: "Member not found!",
      color: 0xfdfd96,
    };

    return interaction.reply({
      embeds: [embed],
    });
  }

  if (
    interaction.member.roles.highest.comparePositionTo(member.roles.highest) <=
      0 &&
    interaction.user.id !== interaction.guild.ownerId
  ) {
    const embed = {
      title: "You cannot kick this user!",
      description: "This user has a higher or equal role than you",
      color: 0xfdfd96,
    };

    return interaction.reply({
      embeds: [embed],
    });
  }

  if (!member.kickable) {
    const embed = {
      title: "I cannot kick this user!",
      color: 0xfdfd96,
    };

    return interaction.reply({
      embeds: [embed],
    });
  }

  const userEmbed = {
    title: "You have been kicked",
    description: `You have been kicked from **${interaction.guild.name}**`,
    fields: [
      {
        name: "Reason",
        value: reason,
      },
    ],
    color: 0xff6961,
  };

  const sentMessageToUser = false;

  try {
    await member.send({
      embeds: [userEmbed],
    });

    sentMessageToUser = true;
  } catch (_) {}

  await member.kick(reason);

  const embed = {
    title: "User Kicked",
    description: `
      :white_check_mark: <@${user.id}> has been kicked
      ${sentMessageToUser ? ":white_check_mark: User has been notified" : ":x: User has not been notified"}
    `,
    fields: [
      {
        name: "Reason",
        value: reason,
      },
    ],
    color: 0xff6961,
  };

  interaction.reply({
    embeds: [embed],
  });

  const guild = await Guild.findOne({ id: interaction.guild.id });

  if (guild) {
    if (guild.log_channel) {
      const channel = await interaction.guild.channels.cache.get(
        guild.log_channel,
      );

      if (channel) {
        const logEmbed = {
          title: "User Kicked",
          description: `
            :white_check_mark: <@${user.id}> has been kicked
            ${sentMessageToUser ? ":white_check_mark: User has been notified" : ":x: User has not been notified"}
          `,
          fields: [
            {
              name: "Reason",
              value: reason,
            },
            {
              name: "Moderator",
              value: `<@${interaction.user.id}>`,
            },
          ],
          color: 0xff6961,
        };

        await channel.send({
          embeds: [logEmbed],
        });
      }
    }
  }
};

export default { data, execute };
