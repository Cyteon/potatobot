import { SlashCommandSubcommandBuilder } from "discord.js";
import EconomyUser from "../../../../lib/models/EconomyUser.js";
import random from "random";

const data = new SlashCommandSubcommandBuilder()
  .setName("diceroll")
  .setDescription("Roll a dice!")
  .addNumberOption((option) =>
    option
      .setName("amount")
      .setDescription("The amount of money to gamble")
      .setRequired(true),
  )
  .addNumberOption((option) =>
    option
      .setName("number")
      .setDescription("The number to bet on")
      .setMinValue(1)
      .setMaxValue(6)
      .setRequired(true),
  );

const execute = async function (interaction) {
  const amount = interaction.options.getNumber("amount");
  const number = interaction.options.getNumber("number");

  let user = await EconomyUser.findOne({ id: interaction.user.id });

  if (!user) {
    user = await EconomyUser.create({
      id: interaction.user.id,
    });
  }

  if (user.balance < amount) {
    return await interaction.reply("You don't have enough money!");
  }

  const winning = random.int(1, 6);

  if (number === winning) {
    user.balance += amount * 1.4;
    await user.save();
    return await interaction.reply(
      `🎲 You rolled a ${winning} and won $${amount * 1.4}!`,
    );
  }

  user.balance -= amount;
  await user.save();

  await interaction.reply(`🎲 You rolled a ${winning} and lost $${amount}!`);
};

export default { data, execute };
