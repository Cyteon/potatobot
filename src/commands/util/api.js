import { SlashCommandBuilder } from "@discordjs/builders";

const data = new SlashCommandBuilder()
  .setName("api")
  .setDescription("Commands for diffrent api stuff")
  .setIntegrationTypes(0, 1)
  .setContexts(0, 1, 2)
  .addSubcommand((subcommand) =>
    subcommand
      .setName("mc-server")
      .setDescription("Get information about a minecraft server")
      .addStringOption((option) =>
        option
          .setName("address")
          .setDescription("The server address")
          .setRequired(true),
      ),
  )
  .addSubcommand((subcommand) =>
    subcommand
      .setName("mc-player")
      .setDescription("Get information about a minecraft player")
      .addStringOption((option) =>
        option
          .setName("username")
          .setDescription("The player username")
          .setRequired(true),
      ),
  );

const execute = async function (interaction) {
  const subcommand = interaction.options.getSubcommand();

  if (subcommand === "mc-server") {
    const address = interaction.options.getString("address");

    const res = await fetch(`https://api.mcsrvstat.us/3/${address}`);

    if (!res.ok) {
      return interaction.reply("An error occurred while fetching the data");
    }

    const data = await res.json();

    if (!data.online) {
      return interaction.reply("The server is offline");
    }

    const embed = {
      title: data.hostname,
      color: 0x56b3fa,
      fields: [
        {
          name: "Players",
          value: `\`\`\`${data.players.online}/${data.players.max}\`\`\``,
        },
        "software" in data
          ? {
              name: "Version",
              value: `\`\`\`${data.version} - ${data.software}\`\`\``,
            }
          : {
              name: "Version",
              value: `\`\`\`${data.version}\`\`\``,
            },
        "list" in data.players
          ? {
              name: "Players",
              value: `\`\`\`${data.players.list.join(", ").slice(0, 1024)}\`\`\``,
            }
          : {
              name: "Players",
              value: "Not available",
            },
      ],
    };

    await interaction.reply({ embeds: [embed] });
  } else if (subcommand === "mc-player") {
    const user = interaction.options.getString("username");

    const embed = {
      title: `${user}'s player`,
      color: 0x56b3fa,
      image: {
        url: `https://mc-heads.net/body/${user}`,
      },
    };

    await interaction.reply({ embeds: [embed] });
  }
};

export default { data, execute };
