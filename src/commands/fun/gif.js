import { SlashCommandBuilder } from "discord.js";
import random from "random";

const data = new SlashCommandBuilder()
  .setName("gif")
  .setDescription("Get a random GIF")
  .setIntegrationTypes(0, 1)
  .setContexts(0, 1, 2);

const execute = async function (interaction) {
  const rand_query = random.choice([
    "funny",
    "cute",
    "cool",
    "weird",
    "random",
    "dead",
    "alive",
    "sad",
    "eepy",
    "death",
    "meme",
    "pepe",
    "discord",
    "game",
    "fortnite",
    "minecraft",
    "netflix",
    "explosion",
    "car",
  ]);

  const response = await fetch(
    `https://tenor.googleapis.com/v2/search?random=true&q=${rand_query}&key=${process.env.TENOR_API_KEY}`,
  );
  const data = await response.json();
  const gif = random.choice(data.results).url;

  return interaction.reply({
    content: gif,
  });
};

export default { data, execute };
