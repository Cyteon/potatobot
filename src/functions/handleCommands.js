import { REST } from "@discordjs/rest";
import { Routes } from "discord-api-types/v9";
import {
  SlashCommandBuilder,
  SlashCommandSubcommandBuilder,
  SlashCommandSubcommandGroupBuilder,
} from "discord.js";
import chalk from "chalk";
import fs from "fs";

const clientId = process.env.APPLICATION_ID;

export default (client) => {
  client.handleCommands = async (commandFolders, path) => {
    console.log(chalk.yellow("Started loading commands."));
    client.commandArray = [];

    for (const folder of commandFolders) {
      const commandFiles = fs
        .readdirSync(`${path}/${folder}`)
        .filter((file) => file.endsWith(".js"));

      const subFolders = fs
        .readdirSync(`${path}/${folder}`, { withFileTypes: true })
        .filter((dirent) => dirent.isDirectory())
        .map((dirent) => dirent.name);

      console.log(`----- ${folder}`);

      for (const file of commandFiles) {
        try {
          const { default: command } = await import(
            `../commands/${folder}/${file}`
          );
          client.commands.set(command.data.name, command);

          if (command.data instanceof SlashCommandBuilder) {
            client.commandArray.push(command.data.toJSON());
          } else {
            client.commandArray.push(command.data);
          }

          console.log(chalk.green(`✅ Loaded command /${chalk.bold(file)}`));
        } catch (error) {
          console.log(
            chalk.red(
              `❌ Error loading command /${chalk.bold(file)}: ${error}`,
            ),
          );
        }
      }

      for (const subFolder of subFolders) {
        try {
          const subCommandFiles = fs
            .readdirSync(`${path}/${folder}/${subFolder}`)
            .filter((file) => file.endsWith(".js") && !file.startsWith("_"));

          let meta = { userInstalled: true };

          if (fs.existsSync(`${path}/${folder}/${subFolder}/_meta.js`)) {
            meta = await import(`../commands/${folder}/${subFolder}/_meta.js`);
          }

          let cmd = new SlashCommandBuilder()
            .setName(subFolder)
            .setDescription("(no description)");

          if (meta.userInstalled) {
            cmd.setIntegrationTypes(0, 1);
            cmd.setContexts(0, 1, 2);
          }

          for (const file of subCommandFiles) {
            try {
              const { default: command } = await import(
                `../commands/${folder}/${subFolder}/${file}`
              );

              cmd.addSubcommand(command.data);

              console.log(
                chalk.green(
                  `✅ Loaded command /${chalk.bold(subFolder)} ${chalk.bold(file)}`,
                ),
              );
            } catch (error) {
              console.log(
                chalk.red(
                  `❌ Error loading command /${chalk.bold(subFolder)} ${chalk.bold(file)}: ${error}`,
                ),
              );
            }
          }

          const groupFolders = fs
            .readdirSync(`${path}/${folder}/${subFolder}`, {
              withFileTypes: true,
            })
            .filter((dirent) => dirent.isDirectory())
            .map((dirent) => dirent.name);

          for (const groupFolder of groupFolders) {
            const groupCommandFiles = fs
              .readdirSync(`${path}/${folder}/${subFolder}/${groupFolder}`)
              .filter((file) => file.endsWith(".js"));

            const group = new SlashCommandSubcommandGroupBuilder()
              .setName(groupFolder)
              .setDescription("(no description)");

            for (const groupFile of groupCommandFiles) {
              try {
                const { default: command } = await import(
                  `../commands/${folder}/${subFolder}/${groupFolder}/${groupFile}`
                );

                group.addSubcommand(command.data);

                console.log(
                  chalk.green(
                    `✅ Loaded command /${chalk.bold(subFolder)} ${chalk.bold(groupFolder)} ${chalk.bold(groupFile)}`,
                  ),
                );
              } catch (error) {
                console.log(
                  chalk.red(
                    `❌ Error loading command /${chalk.bold(subFolder)} ${chalk.bold(groupFolder)} ${chalk.bold(groupFile)}: ${error}`,
                  ),
                );
              }
            }

            cmd.addSubcommandGroup(group);

            console.log(
              chalk.green(
                `✅ Loaded command group /${chalk.bold(subFolder)} ${chalk.bold(groupFolder)}`,
              ),
            );
          }

          const execute = async function (interaction) {
            const subcommand = interaction.options.getSubcommand();
            const group = interaction.options.getSubcommandGroup();

            try {
              if (group) {
                const { default: command } = await import(
                  `../commands/${folder}/${subFolder}/${group}/${subcommand}.js`
                );

                await command.execute(interaction, client);
              } else {
                const { default: command } = await import(
                  `../commands/${folder}/${subFolder}/${subcommand}.js`
                );

                await command.execute(interaction, client);
              }
            } catch (error) {
              console.log(
                chalk.red(
                  `❌ Error executing command /${chalk.bold(subFolder)} ${chalk.bold(subcommand)}: ${error}`,
                ),
              );

              await interaction.reply({
                content: "There was an error while executing this command!",
                ephemeral: true,
              });
            }
          };

          const data = {
            data: cmd,
            execute: execute,
          };

          client.commands.set(subFolder, data);
          client.commandArray.push(cmd.toJSON());

          console.log(
            chalk.green(`✅ Loaded command group /${chalk.bold(subFolder)}`),
          );
        } catch (error) {
          console.log(
            chalk.red(
              `❌ Error loading command group /${chalk.bold(subFolder)}: ${error}`,
            ),
          );
        }
      }
    }

    console.log(`-----`);
    console.log(chalk.green(`Root command count: ${client.commands.size}/100`));
    console.log(
      chalk.green(
        "Total command count: " +
          client.commands.reduce((acc, cmd) => {
            if (cmd.data.options) {
              return (
                acc +
                cmd.data.options.reduce((n, option) => {
                  if (option.type === "SUB_COMMAND") {
                    if (option.options) {
                      option.options.forEach((sub_option) => {
                        if (sub_option.type === "SUB_COMMAND") {
                          return n + 1;
                        }
                      });
                    } else {
                      return n + 1;
                    }
                  } else {
                    return n + 1;
                  }
                }, 0)
              );
            } else {
              return acc + 1;
            }
          }, 0),
      ),
    );

    const rest = new REST({ version: "9" }).setToken(process.env.TOKEN);

    try {
      console.log(chalk.yellow("Started refreshing application (/) commands."));

      await rest.put(Routes.applicationCommands(clientId), {
        body: client.commandArray,
      });

      console.log(
        chalk.green("Successfully reloaded application (/) commands."),
      );
    } catch (error) {
      console.error(error);
    }
  };
};
