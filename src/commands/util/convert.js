import { SlashCommandBuilder } from "discord.js";

const data = new SlashCommandBuilder()
  .setName("convert")
  .setDescription("Commands to convert stuff")
  .setIntegrationTypes(0, 1)
  .setContexts(0, 1, 2)
  .addSubcommand((input) =>
    input
      .setName("mb-gb")
      .setDescription("Convert MB to GB")
      .addNumberOption((input) =>
        input
          .setName("mb")
          .setDescription("The amount of MB to convert")
          .setRequired(true),
      ),
  )
  .addSubcommand((input) =>
    input
      .setName("gb-mb")
      .setDescription("Convert GB to MB")
      .addNumberOption((input) =>
        input
          .setName("gb")
          .setDescription("The amount of GB to convert")
          .setRequired(true),
      ),
  )
  .addSubcommand((input) =>
    input
      .setName("f-c")
      .setDescription("Convert Fahrenheit to Celsius")
      .addNumberOption((input) =>
        input
          .setName("fahrenheit")
          .setDescription("The temperature in Fahrenheit")
          .setRequired(true),
      ),
  )
  .addSubcommand((input) =>
    input
      .setName("c-f")
      .setDescription("Convert Celsius to Fahrenheit")
      .addNumberOption((input) =>
        input
          .setName("celsius")
          .setDescription("The temperature in Celsius")
          .setRequired(true),
      ),
  );

const execute = async function (interaction) {
  const subcommand = interaction.options.getSubcommand();

  if (subcommand === "mb-gb") {
    const mb = interaction.options.getNumber("mb");
    const gb = mb / 1024;

    return interaction.reply({
      content: `${mb}MB is equal to ${gb}GB`,
    });
  } else if (subcommand === "gb-mb") {
    const gb = interaction.options.getNumber("gb");
    const mb = gb * 1024;

    return interaction.reply({
      content: `${gb}GB is equal to ${mb}MB`,
    });
  } else if (subcommand === "f-c") {
    const fahrenheit = interaction.options.getNumber("fahrenheit");
    const celsius = ((fahrenheit - 32) * 5) / 9;

    return interaction.reply({
      content: `${fahrenheit}°F is equal to ${celsius}°C`,
    });
  } else if (subcommand === "c-f") {
    const celsius = interaction.options.getNumber("celsius");
    const fahrenheit = (celsius * 9) / 5 + 32;

    return interaction.reply({
      content: `${celsius}°C is equal to ${fahrenheit}°F`,
    });
  }
};

export default { data, execute };
