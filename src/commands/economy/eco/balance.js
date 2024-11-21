import { SlashCommandSubcommandBuilder } from "discord.js";
import EconomyUser from "../../../lib/models/EconomyUser.js";

const data = new SlashCommandSubcommandBuilder()
  .setName("balance")
  .setDescription("Check your balance!")
  .addUserOption((option) =>
    option.setName("user").setDescription("The user to check the balance of"),
  );

const execute = async function (interaction) {
  let target = interaction.options.getUser("user") || interaction.user;

  let user = await EconomyUser.findOne({ id: target.id }).cache("1 minute");

  if (!user) {
    user = await EconomyUser.create({
      id: target.id,
    });
  }

  await interaction.reply(`💵 **${target.username}** has $${user.balance}!`);
};

export default { data, execute };
