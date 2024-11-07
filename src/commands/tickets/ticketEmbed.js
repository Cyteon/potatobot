import { SlashCommandBuilder } from "@discordjs/builders";
import { PermissionFlagsBits } from "discord.js";

const data = new SlashCommandBuilder()
  .setName("ticketembed")
  .setDescription("Send an embed containg a button to open a ticket")
  .setDefaultMemberPermissions(PermissionFlagsBits.ManageChannels);

const execute = async function (interaction) {
  const embed = {
    color: 0x56b3fa,
    title: "Open a ticket",
    description: "Click the button below to open a ticket",
  };

  const row = {
    type: 1,
    components: [
      {
        type: 2,
        style: 1,
        label: "Open ticket",
        custom_id: "open_ticket",
      },
    ],
  };

  await interaction.channel.send({ embeds: [embed], components: [row] });
  await interaction.reply({
    content: "Ticket embed sent",
    ephemeral: true,
  });
};

export default { data, execute };
