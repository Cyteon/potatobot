import { SlashCommandBuilder } from "discord.js";

const data = new SlashCommandBuilder()
  .setName("insult")
  .setDescription("Insult someone")
  .setIntegrationTypes(0, 1)
  .setContexts(0, 1, 2);

const execute = async function (interaction) {
  const response = await fetch(
    "https://evilinsult.com/generate_insult.php?lang=en&type=json",
  );
  const data = await response.json();
  const insult = data.insult;

  return interaction.reply({
    content: `🔥 ${insult}`,
  });
};

export default { data, execute };
