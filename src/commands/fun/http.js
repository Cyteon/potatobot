import { SlashCommandBuilder } from "discord.js";

const data = new SlashCommandBuilder()
  .setName("http")
  .setDescription("Get animal images representing diffrent HTTP status codes")
  .setIntegrationTypes(0, 1)
  .setContexts(0, 1, 2)
  .addStringOption((option) =>
    option
      .setName("animal")
      .setDescription("The animal to get the image for")
      .setRequired(true)
      .addChoices(
        {
          name: "Cat",
          value: "cat",
        },
        {
          name: "Dog",
          value: "dog",
        },
        {
          name: "Fish",
          value: "fish",
        },
      ),
  )
  .addIntegerOption((option) =>
    option
      .setName("code")
      .setDescription("The HTTP status code to get the image for")
      .setRequired(true),
  );

const execute = async function (interaction) {
  const animal = interaction.options.getString("animal");
  let code = interaction.options.getInteger("code");

  if (code < 100 || code > 599) {
    code = 404;
  }

  if (animal == "cat") {
    return interaction.reply({
      content: `https://http.cat/${code}`,
    });
  } else if (animal == "dog") {
    return interaction.reply({
      content: `https://http.dog/${code}.jpg`,
    });
  } else if (animal == "fish") {
    return interaction.reply({
      content: `https://http.fish/${code}.jpg`,
    });
  }
};

export default { data, execute };
