import { SlashCommandBuilder } from "discord.js";

const data = new SlashCommandBuilder()
  .setName("root")
  .setDescription("Secret D:")
  .setIntegrationTypes(0, 1)
  .setContexts(0, 1, 2)
  .addStringOption((input) =>
    input
      .setName("action")
      .setDescription("dont look here :C")
      .setRequired(true)
      .addChoices(
        {
          name: "💻 Eval | text",
          value: "eval",
        },
        {
          name: "💻 Exec | text",
          value: "exec",
        },
      ),
  )
  .addStringOption((input) =>
    input.setName("text").setDescription("If applicable"),
  );

const execute = async function (interaction) {
  if (interaction.user.id !== process.env.OWNER_ID) {
    return interaction.reply(
      "https://tenor.com/view/pluh-cat-spinning-gif-18263966663003556958",
    );
  }

  const action = interaction.options.getString("action");
  const text = interaction.options.getString("text");

  if (action === "eval") {
    try {
      if (text.includes("await")) {
        const evaled = await eval(`(async () => { ${text} })()`);
        await interaction.reply(`\`\`\`js\n${evaled}\`\`\``);
      } else {
        const evaled = eval(text);
        await interaction.reply(`\`\`\`js\n${evaled}\`\`\``);
      }
    } catch (err) {
      await interaction.reply(`\`\`\`js\n${err}\`\`\``);
    }
  } else if (action === "exec") {
    const { exec } = await import("child_process");

    exec(text, (err, stdout, stderr) => {
      if (err) {
        return interaction.reply(`\`\`\`sh\n${err}\`\`\``);
      }
      if (stderr) {
        return interaction.reply(`\`\`\`sh\n${stderr}\`\`\``);
      }
      interaction.reply(`\`\`\`sh\n${stdout}\`\`\``);
    });
  }
};

export default { data, execute };
