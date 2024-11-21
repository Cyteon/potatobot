import { SlashCommandSubcommandBuilder } from "discord.js";
import EconomyUser from "../../../lib/models/EconomyUser.js";
import random from "random";

const data = new SlashCommandSubcommandBuilder()
  .setName("daily")
  .setDescription("Claim your daily reward!");

const execute = async function (interaction) {
  let user = await EconomyUser.findOne({ id: interaction.user.id }).cache(
    "1 minute",
  );

  if (!user) {
    user = await EconomyUser.create({
      id: interaction.user.id,
      balance: 50,
    });
  }

  let lastDaily = user.lastDaily || 0;

  if (Date.now() - lastDaily < 86400000) {
    return await interaction.reply(
      `🕒 You have already claimed your daily reward! Try again <t:${Math.floor(lastDaily / 1000) + 86400}:R>`,
    );
  }

  const rand = random.int(100, 500);

  user.balance += rand;
  user.lastDaily = Date.now();
  await user.save();

  await interaction.reply(
    `💵 You have claimed your daily reward and got $${rand}!`,
  );
};

export default { data, execute };
