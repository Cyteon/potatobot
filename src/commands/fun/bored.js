import { SlashCommandBuilder } from "discord.js";

const data = new SlashCommandBuilder()
  .setName("bored")
  .setDescription("Get a random activity to do")
  .setIntegrationTypes(0, 1)
  .setContexts(0, 1, 2);

const execute = async function (interaction) {
  const response = await fetch("https://bored-api.appbrewery.com/random");

  if (response.ok) {
    const data = await response.json();

    await interaction.reply({
      embeds: [
        {
          title: data.activity,
          color: 0x56b3fa,
          fields: [
            {
              name: "Type",
              value: data.type.charAt(0).toUpperCase() + data.type.slice(1),
              inline: true,
            },
            {
              name: "Participants",
              value: data.participants,
              inline: true,
            },
            {
              name: "Price",
              value:
                data.price == 0
                  ? "Free"
                  : "$".repeat((data.price * 5).toFixed(0)),
              inline: true,
            },
          ],
        },
      ],
    });
  } else {
    await interaction.reply({
      content: "Failed to fetch a random activity",
      ephemeral: true,
    });
  }
};

export default { data, execute };
