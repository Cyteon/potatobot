import { SlashCommandBuilder } from "discord.js";

const data = new SlashCommandBuilder()
  .setName("advice")
  .setDescription("Get a random piece of advice")
  .setIntegrationTypes(0, 1)
  .setContexts(0, 1, 2);

const execute = async function (interaction) {
  const response = await fetch("https://api.adviceslip.com/advice");
  const data = await response.json();
  const advice = data.slip.advice;

  return interaction.reply({
    content: `🔮 ${advice}`,
  });
};

export default { data, execute };
