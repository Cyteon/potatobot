import { SlashCommandSubcommandBuilder } from "discord.js";
import { RateLimiter } from "discord.js-rate-limiter";
import random from "random";
import EconomyUser from "../../../lib/models/EconomyUser.js";

let rateLimiter = new RateLimiter(1, 10 * 60 * 1000);

const data = new SlashCommandSubcommandBuilder()
  .setName("beg")
  .setDescription("Beg for money!");

const execute = async function (interaction) {
  let limited = rateLimiter.take(interaction.user.id);

  if (limited) {
    return await interaction.reply({
      content: "🕒 You can only beg once every 10 minutes!",
    });
  }

  let user = await EconomyUser.findOne({ id: interaction.user.id });

  if (!user) {
    user = await EconomyUser.create({
      id: interaction.user.id,
    });
  }

  const rand = random.int(10, 100);

  user.balance += rand;
  await user.save();

  await interaction.reply(`🙏 You begged and got $${rand}!`);
};

export default { data, execute };
