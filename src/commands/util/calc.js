import { SlashCommandBuilder } from "discord.js";
import { evaluate } from "mathjs";

const data = new SlashCommandBuilder()
  .setName("calc")
  .setDescription("Calculate a math expression")
  .setIntegrationTypes(0, 1)
  .setContexts(0, 1, 2)
  .addStringOption((option) =>
    option
      .setName("expression")
      .setDescription("The expression to calculate")
      .setRequired(true),
  );

const execute = async function (interaction) {
  const expression = interaction.options.getString("expression");

  try {
    const result = evaluate(expression);

    return interaction.reply({
      embeds: [
        {
          title: "Calculation",
          color: 0x56b3fa,
          fields: [
            {
              name: "Expression",
              value: `\`\`\`js\n${expression}\`\`\``,
            },
            {
              name: "Result",
              value: `\`\`\`js\n${result}\`\`\``,
            },
          ],
        },
      ],
    });
  } catch (error) {
    return interaction.reply({
      content: "⚠️ Failed to calculate the expression",
      ephemeral: true,
    });
  }
};

export default { data, execute };
