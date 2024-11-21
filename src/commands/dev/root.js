import { SlashCommandBuilder } from "discord.js";
import GlobalUser from "../../lib/models/GlobalUser.js";
import Guild from "../../lib/models/Guild.js";
import AiChannels from "../../lib/models/AiChannels.js";
import EconomyUser from "../../lib/models/EconomyUser.js";
import balance from "../economy/eco/balance.js";

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
          name: "📋 List top servers",
          value: "list_top_servers",
        },
        {
          name: "📢 Say | text",
          value: "say",
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
          name: "⛔ AI ban | user, text (reason)",
          value: "ai_ban",
        },
        {
          name: "✅ AI unban | user",
          value: "ai_unban",
        },
        {
          name: "🤖 Enable AI | text (guild id)",
          value: "enable_ai",
        },
        {
          name: "⛔🤖 Disable AI | text (guild id)",
          value: "disable_ai",
        },
        {
          name: "💬 DM | user, text",
          value: "dm",
        },
        {
          name: "📢 AI Announce | text",
          value: "ai_announce",
        },
        {
          name: "💵 Add money | user, number (amount)",
          value: "add_money",
        },
      ),
  )
  .addStringOption((input) =>
    input.setName("text").setDescription("still water"),
  )
  .addUserOption((input) =>
    input.setName("user").setDescription("(those who know)"),
  )
  .addNumberOption((input) => input.setName("number").setDescription("number"));

const execute = async function (interaction) {
  if (interaction.user.id !== process.env.OWNER_ID) {
    return await interaction.reply(
      "https://tenor.com/view/pluh-cat-spinning-gif-18263966663003556958",
    );
  }

  const action = interaction.options.getString("action");
  const text = interaction.options.getString("text");
  const user = interaction.options.getUser("user");
  const number = interaction.options.getNumber("number");

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
      await interaction.reply(
        `\`\`\`js\n${err.toString().slice(0, 1990)}\`\`\``,
      );
    }
  } else if (action === "exec") {
    const { exec } = await import("child_process");

    exec(text, (err, stdout, stderr) => {
      if (err) {
        return interaction.reply(
          `\`\`\`sh\n${err.toString().slice(0, 1990)}\`\`\``,
        );
      }
      if (stderr) {
        return interaction.reply(`\`\`\`sh\n${stderr.slice(0, 1990)}\`\`\``);
      }
      interaction.reply(`\`\`\`sh\n${stdout.slice(0, 1990)}\`\`\``);
    });
  } else if (action === "list_top_servers") {
    let offset = 0;
    let index = 0;

    let guilds = interaction.client.guilds.cache
      .sort((a, b) => b.memberCount - a.memberCount)
      .map((guild) => {
        index += 1;
        return `[${index}] ${guild.name} (${guild.id}) - ${guild.memberCount} members`;
      })
      .slice(offset, 10 + offset);

    const msg = await interaction.reply({
      content: `\`\`\`${guilds.join("\n")}\`\`\``,
      components: [
        {
          type: 1,
          components: [
            {
              type: 2,
              style: 1,
              label: "Previous",
              custom_id: "previous-" + interaction.id,
            },
            {
              type: 2,
              style: 1,
              label: "Next",
              custom_id: "next-" + interaction.id,
            },
          ],
        },
      ],
    });

    const filter = (i) => i.user.id === interaction.user.id;

    const collector = msg.createMessageComponentCollector({
      filter,
      time: 60000,
    });

    collector.on("collect", async (i) => {
      if (i.customId === "previous-" + interaction.id) {
        offset = Math.max(0, offset - 10);
      } else if (i.customId === "next-" + interaction.id) {
        offset = Math.min(
          Math.max(10, interaction.client.guilds.cache.size) - 10,
          offset + 10,
        );
      }

      index = offset;

      guilds = interaction.client.guilds.cache
        .sort((a, b) => b.memberCount - a.memberCount)
        .map((guild) => {
          index += 1;
          return `[${index}] ${guild.name} (${guild.id}) - ${guild.memberCount} members`;
        })
        .slice(offset, 10 + offset);

      await i.update({
        content: `\`\`\`${guilds.join("\n")}\`\`\``,
      });
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
  } else if (action === "ai_ban") {
    let data = await GlobalUser.findOne({ id: user.id }).exec();

    if (!data) {
      data = await GlobalUser.create({
        id: user.id,
        ai_ignore: true,
        ai_ignore_reason: text || "No reason provided",
      });
    } else {
      data.ai_ignore = true;
      data.ai_ignore_reason = text || "No reason provided";
      await data.save();
    }

    await interaction.reply({
      content: `:white_check_mark: **${user.tag}** is now banned from using AI!`,
    });
  } else if (action === "ai_unban") {
    let data = await GlobalUser.findOne({ id: user.id }).exec();

    if (!data) {
      return await interaction.reply({
        content: `:x: User ${user.tag} is not banned from AI!`,
      });
    }

    data.ai_ignore = false;
    data.ai_ignore_reason = "";
    await data.save();

    await interaction.reply({
      content: `:white_check_mark: **${user.tag}** is now allowed to use AI!`,
    });
  } else if (action === "enable_ai") {
    let guildData = await Guild.findOne({
      id: text || interaction.guild.id,
    }).exec();

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
    let guildData = await Guild.findOne({
      id: text || interaction.guild.id,
    }).exec();

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
  } else if (action === "say") {
    await interaction.channel.send(text);
  } else if (action === "dm") {
    await user.send(text);

    await interaction.reply({
      content: `:white_check_mark: Sent message to ${user.tag}`,
      ephemeral: true,
    });
  } else if (action === "ai_announce") {
    await interaction.deferReply();

    const channels = await AiChannels.findOne({}).exec();

    if (!channels) {
      return await interaction.reply({
        content: `:x: No AI channels found!`,
      });
    }

    channels.ai_channels.forEach(async (channel) => {
      const ch = interaction.client.channels.cache.get(channel);

      if (ch) {
        try {
          await ch.send({
            embeds: [
              {
                description: text,
                color: 0x56b3fa,
              },
            ],
          });
        } catch (e) {
          console.error(
            `Error sending announcement to ${ch.name}: ${e.message}`,
          );
        }
      }
    });

    await interaction.editReply({
      content: `:white_check_mark: Sent announcement to AI channels!`,
    });
  } else if (action === "add_money") {
    let target = await EconomyUser.findOne({ id: user.id });

    if (!target) {
      target = await EconomyUser.create({
        id: user.id,
      });
    }

    if (number == 0) {
      target.balance = 0;
    } else {
      target.balance += number;
    }

    await target.save();

    await interaction.reply(
      `💵 Added **$${number}** to **${user.username}**! They now have **$${target.balance}**!`,
    );
  }
};

export default { data, execute };
