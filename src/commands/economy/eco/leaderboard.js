import { SlashCommandSubcommandBuilder } from "discord.js";
import EconomyUser from "../../../lib/models/EconomyUser.js";

const data = new SlashCommandSubcommandBuilder()
  .setName("leaderboard")
  .setDescription("Check the leaderboard!");

const execute = async function (interaction) {
  const top10 = await EconomyUser.find().sort({ balance: -1 }).limit(10);
  const user = await EconomyUser.findOne({ id: interaction.user.id });

  const embed = {
    title: "Economy Leaderboard",
    description: top10
      .map((user, index) => {
        const arrow = user.id == interaction.user.id ? " ▶️ " : " ";

        return `${index + 1}.${arrow}<@${user.id}>\n> $${user.balance}`;
      })
      .join("\n"),
    color: 0x56b3fa,
    footer: {
      text: `Your balance: $${user.balance}`,
    },
  };

  await interaction.reply({ embeds: [embed] });
};

export default { data, execute };
