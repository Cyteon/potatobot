import {
  ThreadAutoArchiveDuration,
  ChannelType,
  PermissionFlagsBits,
} from "discord.js";
import GlobalUser from "../lib/models/GlobalUser.js";
import Guild from "../lib/models/Guild.js";

const ai_commands = ["imagine"];

export default {
  name: "interactionCreate",
  async execute(interaction, client) {
    if (interaction.isCommand()) {
      const command = client.commands.get(interaction.commandName);

      if (!command) return;

      let user = await GlobalUser.findOne({ id: interaction.user.id });

      if (!user) {
        user = await GlobalUser.create({
          id: interaction.user.id,
        });
      }

      if (user.blacklisted && command.data.name !== "root") {
        return await interaction.reply({
          content: `:no_entry: You are blacklisted from using commands! Reason: ${user.blacklist_reason}`,
          ephemeral: true,
        });
      }

      if (
        ai_commands.includes(command.data.name) &&
        user.ai_ignore /* ai_ignore is AI ban */
      ) {
        return await interaction.reply({
          content: `:no_entry: You are banned from using AI commands! Reason: ${user.ai_ignore_reason}`,
          ephemeral: true,
        });
      }

      try {
        await command.execute(interaction, client);
      } catch (error) {
        console.log(error);
        try {
          await interaction.reply({
            content: "There was an error while executing this command!",
            ephemeral: true,
          });
        } catch (error) {
          console.log(
            "Error while handling error in interactionCreate event: ",
            error,
          );
        }
      }
    } else if (interaction.isButton()) {
      if (interaction.customId == "open_ticket") {
        const guildData = await Guild.findOne({ id: interaction.guild.id });

        if (!guildData) {
          return await interaction.reply({
            content: "This server does not have tickets set up!",
            ephemeral: true,
          });
        }

        if (!guildData.ticketChannel) {
          return await interaction.reply({
            content: "This server does not have tickets set up!",
            ephemeral: true,
          });
        }

        const ticketChannel = interaction.guild.channels.cache.get(
          guildData.ticketChannel,
        );

        if (!ticketChannel) {
          return await interaction.reply({
            content: "This server does not have tickets set up correctly!",
            ephemeral: true,
          });
        }

        const ticketLogChannel = interaction.guild.channels.cache.get(
          guildData.ticketLogChannel,
        );

        if (!ticketLogChannel) {
          return await interaction.reply({
            content: "This server does not have tickets set up correctly!",
          });
        }

        const existingTicket = ticketChannel.threads.cache.find(
          (thread) =>
            thread.name === `ticket-${interaction.user.username}` &&
            thread.archived === false,
        );

        if (existingTicket) {
          return await interaction.reply({
            content: "You already have an open ticket!",
            ephemeral: true,
          });
        }

        // tickets channel is a text channel instead of a category btw
        const ticket = await ticketChannel.threads.create({
          name: `ticket-${interaction.user.username}`,
          autoArchiveDuration: ThreadAutoArchiveDuration.ThreeDays,
          type: ChannelType.PrivateThread,
          reason: `Ticket created by ${interaction.user.tag}`,
        });

        await ticket.members.add(interaction.user.id);

        const msg = await ticket.send({
          content: `<@${interaction.user.id}>`,
          embeds: [
            {
              color: 0x56b3fa,
              title: "Ticket opened",
              description: `Please describe your issue here. Staff will be with you shortly.`,
            },
          ],
          components: [
            {
              type: 1,
              components: [
                {
                  type: 2,
                  style: 4,
                  emoji: "🔒",
                  label: "Close ticket",
                  custom_id: "close_ticket",
                },
              ],
            },
          ],
        });

        await msg.pin();

        await interaction.reply({
          content: "Ticket created!",
          ephemeral: true,
        });

        await ticketLogChannel.send({
          embeds: [
            {
              title: "Ticket Created",
              description: `A ticket has been made by <@${interaction.user.id}>`,
              color: 0x56b3fa,
              footer: {
                text: ticket.id,
              },
            },
          ],
          components: [
            {
              type: 1,
              components: [
                {
                  type: 2,
                  style: 1,
                  emoji: "🔓",
                  label: "Join ticket",
                  custom_id: "join_ticket",
                },
              ],
            },
          ],
        });
      } else if (interaction.customId == "close_ticket") {
        if (
          !interaction.member.permissions.has(
            PermissionFlagsBits.ManageChannels,
          )
        ) {
          if (
            interaction.user.username !== interaction.channel.name.split("-")[1]
          ) {
            return interaction.reply({
              content: "You do not have permission to use this command",
              ephemeral: true,
            });
          }
        }

        await interaction.channel.send({
          embeds: [
            {
              title: "Ticket Closed",
              description: `This ticket has been closed by <@${interaction.user.id}>`,
              color: 0xff6961,
            },
          ],
        });

        await interaction.channel.setArchived(true);
      } else if (interaction.customId == "join_ticket") {
        const id = interaction.message.embeds[0].footer.text;

        const ticket = interaction.guild.channels.cache.get(id);

        if (!ticket) {
          return interaction.reply({
            content: "This ticket no longer exists!",
            ephemeral: true,
          });
        }

        await ticket.members.add(interaction.user.id);

        await ticket.send({
          content: `<@${interaction.user.id}> has joined the ticket!`,
        });

        await interaction.reply({
          content: "You have joined the ticket!",
          ephemeral: true,
        });
      }
    }
  },
};
