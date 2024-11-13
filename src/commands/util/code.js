import {
  SlashCommandBuilder,
  ModalBuilder,
  TextInputBuilder,
  TextInputStyle,
  ActionRowBuilder,
} from "discord.js";

const data = new SlashCommandBuilder()
  .setName("code")
  .setDescription("Run some code in (almost) any language")
  .setIntegrationTypes(0, 1)
  .setContexts(0, 1, 2)
  .addStringOption((option) =>
    option
      .setName("language")
      .setDescription("The language to run the code in")
      .setRequired(true),
  );

const execute = async function (interaction) {
  const language = interaction.options.getString("language");

  const modal = new ModalBuilder()
    .setCustomId(`code_${interaction.id}`)
    .setTitle("Code Execution");

  const codeInput = new TextInputBuilder()
    .setCustomId("codeInput")
    .setLabel("Code")
    .setPlaceholder("Enter your code here")
    .setStyle(TextInputStyle.Paragraph)
    .setMinLength(1)
    .setMaxLength(2000)
    .setRequired(true);

  const row = new ActionRowBuilder().addComponents(codeInput);
  modal.addComponents(row);

  await interaction.showModal(modal);

  const modalSubmitInteraction = await interaction.awaitModalSubmit({
    time: 60_000,
  });

  const code = modalSubmitInteraction.fields.getTextInputValue("codeInput");

  try {
    const response = await fetch(`https://emkc.org/api/v2/piston/execute`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        language,
        version: "*",
        files: [
          {
            name: "main",
            content: code,
          },
        ],
      }),
    });

    if (response.ok) {
      const data = await response.json();

      let output = `${(data.run.stdout || data.run.output).slice(0, 1950)}${(data.run.stdout || data.run.output) > 1950 ? "..." : ""}`;

      return modalSubmitInteraction.reply({
        content: `🔥 Output:\n\`\`\`${language}\n${output}\`\`\``,
      });
    } else {
      const data = await response.json();

      const output = ` ${data.message.slice(0, 1950)}${data.message > 1950 ? "..." : ""}`;

      return modalSubmitInteraction.reply({
        content: `⚠️ Failed to execute the code: \`\`\`${language}\n${output}\`\`\``,
      });
    }
  } catch (error) {
    const msg = `${error.message.slice(0, 1950)}${error.message > 1950 ? "..." : ""}`;

    return modalSubmitInteraction.reply({
      content: `⚠️ Failed to execute the code: \`\`\`${language}\n${msg}\`\`\``,
    });
  }
};

export default { data, execute };
