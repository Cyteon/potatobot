import { SlashCommandSubcommandBuilder } from "discord.js";
import { RateLimiter } from "discord.js-rate-limiter";
import random from "random";
import EconomyUser from "../../../lib/models/EconomyUser.js";

const rateLimiter = new RateLimiter(1, 60 * 60 * 1000);

const data = new SlashCommandSubcommandBuilder()
  .setName("rob")
  .setDescription("Rob someone for money!")
  .addUserOption((option) =>
    option
      .setName("user")
      .setDescription("The user you want to rob")
      .setRequired(true),
  );

const execute = async function (interaction) {
  const user = interaction.options.getUser("user");

  let me = await EconomyUser.findOne({ id: interaction.user.id });
  let target = await EconomyUser.findOne({
    id: user.id,
  });

  if (!target) {
    return await interaction.reply("🤷‍♂️ That user doesn't have any money!");
  }

  if (!me) {
    me = await EconomyUser.create({
      id: interaction.user.id,
    });
  }

  if (target.balance < 50) {
    return await interaction.reply(
      "🤷‍♂️ That user doesn't have enough money to be worth robbing!",
    );
  }

  const limited = rateLimiter.take(interaction.user.id);

  if (limited) {
    return await interaction.reply({
      content: "🕒 You can only rob once every hour!",
    });
  }

  if (target.lastRobbed && Date.now() - target.lastRobbed < 60 * 60 * 1000) {
    return await interaction.reply(
      `🕒 That user can be robbed again in <t:${Math.floor(target.lastRobbed / 1000) + 3600}:R>!`,
    );
  }

  let max = Math.floor(Math.min(target.balance / 20, 1000));
  let min = Math.floor(Math.min(target.balance / 50, 100));
  console.log(max);
  let rand = random.int(min, max);

  if (random.int(0, 100) < 10) {
    let loosing = random.int(0, Math.floor(me.balance / 20));

    me.balance -= loosing;
    target.balance += loosing;
    await me.save();
    await target.save();
    return await interaction.reply(
      `🔫 You tried to rob **${user.username}** but they caught you and you lost $${Math.abs(rand)}!`,
    );
  }

  let failNoLoss = random.int(0, 100) < 15;

  if (failNoLoss) {
    await target.save();
    return await interaction.reply(
      `🔫 You tried to rob **${user.username}** but they caught you and you didn't lose any money!`,
    );
  }

  me.balance += rand;
  target.balance -= rand;
  target.lastRobbed = Date.now();
  await me.save();
  await target.save();

  await interaction.reply(
    `💵 You successfully robbed **${user.username}** and got $${rand}!`,
  );

  try {
    await user.send(
      `⚠️ You were robbed by **${interaction.user.username}** and lost $${rand}!`,
    );
  } catch (_) {}
};

export default { data, execute };
