import { REST } from "@discordjs/rest";
import { Routes } from "discord-api-types/v9";
import { SlashCommandBuilder } from "discord.js";
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

          console.log(chalk.green(`✅ Loaded command ${chalk.bold(file)}`));
        } catch (error) {
          console.log(
            chalk.red(`❌ Error loading command ${chalk.bold(file)}: ${error}`),
          );
        }
      }
    }

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
