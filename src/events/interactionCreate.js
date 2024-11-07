import { ThreadAutoArchiveDuration, ChannelType } from "discord.js";
import GlobalUser from "../lib/models/GlobalUser.js";
import Guild from "../lib/models/Guild.js";

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
            content: "This server does not have tickets set up!",
            ephemeral: true,
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

        const supportRole = interaction.guild.roles.cache.get(
          guildData.tickets_support_role,
        );

        await ticket.send({
          content: `<@${interaction.user.id}> <@&${supportRole.id}>`,
          embeds: [
            {
              color: 0x56b3fa,
              title: "Ticket opened",
              description: `Please describe your issue here. Staff will be with you shortly.`,
            },
          ],
        });

        await interaction.reply({
          content: "Ticket created!",
          ephemeral: true,
        });
      }
    }
  },
};
