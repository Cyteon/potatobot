import { SlashCommandBuilder, AttachmentBuilder } from "discord.js";

const data = new SlashCommandBuilder()
  .setName("archive")
  .setDescription("Archive a set amount of messages")
  .addNumberOption((option) =>
    option
      .setName("amount")
      .setDescription("The amount of messages to archive")
      .setRequired(true)
      .setMinValue(2)
      .setMaxValue(100),
  );

const execute = async function (interaction) {
  const amount = interaction.options.getNumber("amount");

  const messages = await interaction.channel.messages.fetch({
    limit: amount,
  });

  let content = `Archive of ${amount} messages from #${interaction.channel.name} (${interaction.channel.id}) @ ${new Date()}:\n\n`;

  const maxLength = messages.reduce((max, message) => {
    const timestamp = message.createdAt
      .toISOString()
      .replace("T", " ")
      .replace("Z", "");
    const author = message.author.tag;

    return Math.max(max, `${timestamp} | ${author} |`.length);
  }, 0);

  // tope off values

  for (const message of Array.from(messages.values()).reverse()) {
    const timestamp = message.createdAt
      .toISOString()
      .replace("T", " ")
      .replace("Z", "");
    const author = message.author.tag;

    const startLength = `${timestamp} | ${author} |`.length;

    content += `${timestamp} | ${author}${" ".repeat(maxLength - startLength)} | ${message.content}\n`;
  }

  const attachment = new AttachmentBuilder()
    .setName("archive.txt")
    .setFile(Buffer.from(content));

  return interaction.reply({
    files: [attachment],
  });
};

export default { data, execute };
