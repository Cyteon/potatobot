import { SlashCommandBuilder } from "@discordjs/builders";

import packageInfo from "../../../package.json" with { type: "json" };

const data = new SlashCommandBuilder()
  .setName("botinfo")
  .setDescription("Get some information about the bot")
  .setIntegrationTypes(0, 1)
  .setContexts(0, 1, 2);

const execute = async function (interaction) {
  const uptime = process.uptime();
  const days = Math.floor(uptime / 86400);
  const hours = Math.floor(uptime / 3600) % 24;
  const minutes = Math.floor(uptime / 60) % 60;
  const seconds = Math.floor(uptime) % 60;

  let command_count = 0;

  interaction.client.commands.forEach((command) => {
    if (command.data.options) {
      command.data.options.forEach((option) => {
        if (option.type === "SUB_COMMAND") {
          if (option.options) {
            option.options.forEach((sub_option) => {
              if (sub_option.type === "SUB_COMMAND") {
                command_count += 1;
              }
            });
          } else {
            command_count += 1;
          }
        } else {
          command_count += 1;
        }
      });
    } else {
      command_count += 1;
    }
  });

  const embed = {
    title: "Bot Information",
    color: 0x56b3fa,
    fields: [
      {
        name: "Version",
        value: `\`\`\`${packageInfo.version}\`\`\``,
        inline: true,
      },
      {
        name: "Uptime",
        value: `\`\`\`${days}d ${hours}h ${minutes}m ${seconds}s\`\`\``,
        inline: true,
      },
      {
        name: "Ping",
        value: `\`\`\`${interaction.client.ws.ping}ms\`\`\``,
        inline: true,
      },
      {
        name: "Servers",
        value: `\`\`\`${interaction.client.guilds.cache.size}\`\`\``,
        inline: true,
      },
      {
        name: "Users",
        value: `\`\`\`${interaction.client.users.cache.size}\`\`\``,
        inline: true,
      },
      {
        name: "Shards",
        value: `\`\`\`${interaction.client.ws.shards.size}\`\`\``,
        inline: true,
      },
      {
        name: "Commands",
        value: `\`\`\`${command_count}\`\`\``,
        inline: true,
      },
    ],
    footer: {
      text: `Made by cyteon @ https://github.com/cyteon`,
    },
  };

  await interaction.reply({ embeds: [embed] });
};

export default { data, execute };
