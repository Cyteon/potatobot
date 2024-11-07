import { SlashCommandBuilder } from "@discordjs/builders";
import { EmbedBuilder, PermissionFlagsBits } from "discord.js";
import random from "random";

const data = new SlashCommandBuilder()
  .setName("giveaway")
  .setDescription("commands for giveaway")
  .addSubcommand((subcommand) =>
    subcommand
      .setName("start")
      .setDescription("Start a giveaway!")
      .addStringOption((option) =>
        option
          .setName("reward")
          .setDescription("The reward for the giveaway")
          .setRequired(true),
      )
      .addIntegerOption((option) =>
        option
          .setName("winners")
          .setDescription("The number of winners")
          .setRequired(false),
      )
      .addStringOption((option) =>
        option.setName("time").setDescription("The time for the giveaway"),
      ),
  )
  .addSubcommand((subcommand) =>
    subcommand
      .setName("end")
      .setDescription("End a giveaway and choose a winner!")
      .addStringOption((option) =>
        option
          .setName("message_id")
          .setDescription("The message ID of the giveaway")
          .setRequired(true),
      ),
  )
  .setDefaultMemberPermissions(PermissionFlagsBits.ManageMessages);

async function startGiveaway(interaction) {
  const reward = interaction.options.getString("reward");
  const winners = interaction.options.getInteger("winners") || 1;
  const time = interaction.options.getString("time");

  const embed = new EmbedBuilder()
    .setTitle("Giveaway!")
    .setDescription(reward)
    .addFields([
      {
        name: "Winners",
        value: winners.toString(),
      },
      {
        name: "Time",
        value: time || "Not set",
      },
    ])
    .setFooter({
      text: "React with 🎁 to participate!",
    })
    .setColor(0x56b3fa);

  const message = await interaction.reply({
    embeds: [embed],
    fetchReply: true,
  });

  await message.react("🎁");
}

async function endGiveaway(interaction) {
  const messageId = interaction.options.getString("message_id");
  const message = await interaction.channel.messages.fetch(messageId);

  const winners = message.embeds[0].fields.find(
    (field) => field.name === "Winners",
  ).value;

  const users = [];
  const reaction = message.reactions.cache.get("🎁");

  if (reaction) {
    const usersIterator = await reaction.users.fetch();
    usersIterator.forEach((user) => {
      if (user.id !== interaction.client.user.id) {
        users.push(user);
      }
    });

    if (users.length === 0) {
      return interaction.reply("No users participated in the giveaway.");
    }

    if (winners == 1) {
      const winner = random.choice(users);

      const embed = new EmbedBuilder()
        .setTitle("Giveaway ended!")
        .setDescription(`The winner is: ${winner} 🎉🎉🎉`)
        .setColor(0x56b3fa);

      await interaction.reply({ content: winner.toString(), embeds: [embed] });
    } else {
      let winnersList = [];

      for (let i = 0; i < winners; i++) {
        const winner = random.choice(users);
        winnersList.push(winner.toString());

        users.splice(users.indexOf(winner), 1);

        if (users.length === 0) {
          break;
        }
      }

      const embed = new EmbedBuilder()
        .setTitle("Giveaway ended!")
        .setDescription(
          "The winners are: " + winnersList.join(", ") + " 🎉🎉🎉",
        )
        .setColor(0x56b3fa);

      await interaction.reply({
        embeds: [embed],
        content: winnersList.join(", "),
      });
    }
  } else {
    await interaction.reply("No reactions found on this message.");
  }
}

const execute = async function (interaction) {
  const subcommand = interaction.options.getSubcommand();

  switch (subcommand) {
    case "start":
      await startGiveaway(interaction);
      break;
    case "end":
      await endGiveaway(interaction);
      break;
  }
};

export default { data, execute };
