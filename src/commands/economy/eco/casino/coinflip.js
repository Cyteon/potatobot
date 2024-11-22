import { SlashCommandSubcommandBuilder } from "discord.js";
import EconomyUser from "../../../../lib/models/EconomyUser.js";
import random from "random";

const data = new SlashCommandSubcommandBuilder()
  .setName("coinflip")
  .setDescription("Gamble on a coin flip")
  .addNumberOption((option) =>
    option
      .setName("amount")
      .setDescription("The amount of money to gamble")
      .setRequired(true),
  )
  .addStringOption((option) =>
    option.setName("choice").setDescription("Heads or tails").addChoices(
      {
        name: "Tails",
        value: "heads",
      },
      {
        name: "Heads",
        value: "heads",
      },
    ),
  );

const execute = async function (interaction) {
  const amount = interaction.options.getNumber("amount");
  const side =
    interaction.options.getString("choice") ||
    random.choice(["heads", "tails"]);

  if (amount < 1) {
    return await interaction.reply("You can't gamble less than $1!");
  }

  let user = await EconomyUser.findOne({ id: interaction.user.id });

  if (!user) {
    user = await EconomyUser.create({
      id: interaction.user.id,
    });
  }

  if (amount > user.balance) {
    return await interaction.reply("You don't have enough money!");
  }

  const result = random.choice(["heads", "tails"]);

  if (side === result) {
    user.balance += amount;
    await user.save();
    return await interaction.reply(
      `The coin landed on **${result}** 🪙 You won **$${amount}** :D`,
    );
  }

  user.balance -= amount;
  await user.save();

  await interaction.reply(
    `The coin landed on **${result}** 🪙 You lost **$${amount}** D:`,
  );
};

export default { data, execute };
