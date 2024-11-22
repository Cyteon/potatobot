import {
  SlashCommandSubcommandBuilder,
  ActionRowBuilder,
  ButtonBuilder,
  ButtonStyle,
} from "discord.js";
import EconomyUser from "../../../lib/models/EconomyUser.js";

const data = new SlashCommandSubcommandBuilder()
  .setName("pay")
  .setDescription("Give someone some money")
  .addUserOption((input) =>
    input
      .setName("user")
      .setDescription("The user to give money to")
      .setRequired(true),
  )
  .addIntegerOption((input) =>
    input
      .setName("amount")
      .setDescription("The amount of money to give")
      .setRequired(true),
  );

const execute = async function (interaction) {
  let target = interaction.options.getUser("user");
  let amount = interaction.options.getInteger("amount");

  let myData = await EconomyUser.findOne({ id: interaction.user.id });
  let targetData = await EconomyUser.findOne({ id: target.id });

  if (!targetData) {
    targetData = await EconomyUser.create({
      id: target.id,
    });
  }

  if (!myData) {
    myData = await EconomyUser.create({
      id: interaction.user.id,
    });
  }

  if (myData.balance < amount) {
    return await interaction.reply("You don't have enough money!");
  }

  if (amount < 1) {
    return await interaction.reply("You can't pay less than $1!");
  }

  if (amount < 5000) {
    myData.balance -= amount;
    targetData.balance += amount;
    await myData.save();
    await targetData.save();

    return await interaction.reply(
      `You gave **${target.username}** $${amount}!`,
    );
  }

  let embed = {
    title: "Authorize Transaction",
    description: `
⚠️ You are about to make a large transaction ⚠️

**You will give <@${target.id}>:**
\`\`\`
$${amount}
\`\`\`
Are you sure you want to proceed?
    `,
    color: 0xff6961,
  };

  const confirmButton = new ButtonBuilder()
    .setCustomId(`confirm-${interaction.id}`)
    .setLabel("Confirm")
    .setEmoji("✅")
    .setStyle(ButtonStyle.Primary);

  const cancelButton = new ButtonBuilder()
    .setCustomId(`cancel-${interaction.id}`)
    .setLabel("Cancel")
    .setEmoji("❎")
    .setStyle(ButtonStyle.Danger);

  const row = new ActionRowBuilder().addComponents(confirmButton, cancelButton);

  const msg = await interaction.reply({ embeds: [embed], components: [row] });

  const collector = msg.createMessageComponentCollector({
    time: 10_000,
    filter: (i) => i.user.id === interaction.user.id,
  });

  let collected = false;

  collector.on("collect", async (i) => {
    collected = true;

    if (i.customId === `confirm-${interaction.id}`) {
      myData.balance -= amount;
      targetData.balance += amount;
      await myData.save();
      await targetData.save();

      await i.update({
        content: `You gave **${target.username}** $${amount}!`,
        embeds: [],
        components: [],
      });
    } else if (i.customId === `cancel-${interaction.id}`) {
      await i.update({
        content: "Transaction canceled.",
        embeds: [],
        components: [],
      });
    }
  });

  collector.on("end", async (_) => {
    if (!collected) {
      await msg.edit({
        content: "Transaction timed out.",
        embeds: [],
        components: [],
      });
    }
  });
};

export default { data, execute };
