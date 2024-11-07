import { SlashCommandBuilder } from "discord.js";
import GlobalUser from "../../lib/models/GlobalUser.js";
import Guild from "../../lib/models/Guild.js";

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
        {
          name: "⛔ Blacklist | user, text (reason)",
          value: "blacklist",
        },
        {
          name: "✅ Unblacklist | user",
          value: "unblacklist",
        },
        {
          name: "🤖 Enable AI | text (guild id)",
          value: "enable_ai",
        }, {
          name: "⛔🤖 Disable AI | text (guild id)",
          value: "disable_ai",
        }
      ),
  )
  .addStringOption((input) =>
    input.setName("text").setDescription("If applicable"),
  )
  .addUserOption((input) =>
    input.setName("user").setDescription("If applicable"),
  );

const execute = async function (interaction) {
  if (interaction.user.id !== process.env.OWNER_ID) {
    return interaction.reply(
      "https://tenor.com/view/pluh-cat-spinning-gif-18263966663003556958",
    );
  }

  const action = interaction.options.getString("action");
  const text = interaction.options.getString("text");
  const user = interaction.options.getUser("user");

  if (action === "eval") {
    try {
      if (text.includes("await")) {
        const evaled = await eval(`(async () => { ${text} })()`);
        await interaction.reply(`\`\`\`js\n${evaled.slice(0, 1990)}\`\`\``);
      } else {
        const evaled = eval(text);
        await interaction.reply(`\`\`\`js\n${evaled.slice(0, 1990)}\`\`\``);
      }
    } catch (err) {
      await interaction.reply(`\`\`\`js\n${err.slice(0, 1990)}\`\`\``);
    }
  } else if (action === "exec") {
    const { exec } = await import("child_process");

    exec(text, (err, stdout, stderr) => {
      if (err) {
        return interaction.reply(`\`\`\`sh\n${err.slice(0, 1990)}\`\`\``);
      }
      if (stderr) {
        return interaction.reply(`\`\`\`sh\n${stderr.slice(0, 1990)}\`\`\``);
      }
      interaction.reply(`\`\`\`sh\n${stdout.slice(0, 1990)}\`\`\``);
    });
  } else if (action === "blacklist") {
    let data = await GlobalUser.findOne({ id: user.id }).exec();

    if (!data) {
      data = await GlobalUser.create({
        id: user.id,
        blacklisted: true,
        blacklist_reason: text || "No reason provided",
      });
    } else {
      data.blacklisted = true;
      data.blacklist_reason = text || "No reason provided";
      await data.save();
    }

    await interaction.reply({
      content: `:white_check_mark: Blacklisted user ${user.tag}!`,
    });
  } else if (action === "unblacklist") {
    let data = await GlobalUser.findOne({ id: user.id }).exec();

    if (!data) {
      return await interaction.reply({
        content: `:x: User ${user.tag} is not blacklisted!`,
      });
    }

    data.blacklisted = false;
    data.blacklist_reason = "";
    await data.save();

    await interaction.reply({
      content: `:white_check_mark: Unblacklisted user ${user.tag}!`,
    });
  } else if (action === "enable_ai") {
    let guildData = await Guild.findOne({ id: text || interaction.guild.id }).exec();

    if (!guildData) {
      guildData = await Guild.create({
        id: text,
        ai_access: true,
      });
    } else {
      guildData.ai_access = true;
      await guildData.save();
    }

    await interaction.reply({
      content: `:white_check_mark: AI enabled for guild ${text || "current guild"}`,
    });
  } else if (action === "disable_ai") {
    let guildData = await Guild.findOne({ id: text || interaction.guild.id }).exec();

    if (!guildData) {
      return await interaction.reply({
        content: `:x: AI is not enabled for guild ${text}`,
      });
    }

    guildData.ai_access = false;

    await guildData.save();

    await interaction.reply({
      content: `:white_check_mark: AI disabled for guild ${text || "current guild"}`,
    });
  }
};

export default { data, execute };
