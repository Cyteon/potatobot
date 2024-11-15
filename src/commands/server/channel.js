import { SlashCommandBuilder } from "discord.js";
import Guild from "../../lib/models/Guild.js";

const data = new SlashCommandBuilder()
  .setName("channel")
  .setDescription("Commands to set channels for the bot")
  .addSubcommand((subcommand) =>
    subcommand
      .setName("logs")
      .setDescription("Which channel to send logs to")
      .addChannelOption((option) =>
        option
          .setName("channel")
          .setDescription("The channel to send logs to")
          .setRequired(true),
      ),
  );

const execute = async function (interaction) {
  const subcommand = interaction.options.getSubcommand();
  const channel = interaction.options.getChannel("channel");

  if (subcommand == "logs") {
    let guildData = await Guild.findOne({ id: interaction.guildId });

    if (!guildData) {
      guildData = new Guild({ id: interaction.guildId });
    }

    guildData.log_channel = channel.id;

    await guildData.save();

    await interaction.reply(`Set the log channel to <#${channel.id}>`);
  }
};

export default { data, execute };
