/*
 * Copyright (C) 2024 Cyteon
 * Repository: https://github.com/cyteon/potatobot
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <https://www.gnu.org/licenses/>.
 *
 * This copyright notice and permission notice shall not be removed,
 * altered, or obscured in any distribution of this software.
 */

import {
  Client,
  GatewayIntentBits,
  Collection,
  WebhookClient,
} from "discord.js";
import fetch from "node-fetch";
import fs from "fs";
import chalk from "chalk";
import mongoose from "mongoose";
import cache from "ts-cache-mongoose";
import packageData from "../package.json" with { type: "json" };
import figlet from "figlet";
import runServer from "./server.js";

import dotenv from "dotenv";
dotenv.config();

console.log(chalk.blue("Starting..."));

cache.init(mongoose, {
  engine: "memory",
});

mongoose.connect(process.env.MONGODB_URL);

console.log(chalk.green("Connected to MongoDB."));

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
    GatewayIntentBits.GuildModeration,
  ],
});

const errorWebhook = new WebhookClient({
  url: process.env.ERROR_WEBHOOK,
});

client.commands = new Collection();

const functions = fs
  .readdirSync("./src/functions")
  .filter((file) => file.endsWith(".js"));
const eventFiles = fs
  .readdirSync("./src/events")
  .filter((file) => file.endsWith(".js"));
const commandFolders = fs.readdirSync("./src/commands");

(async () => {
  await figlet(
    packageData.name,
    {
      horizontalLayout: "full",
    },
    (err, data) => {
      if (err) {
        console.log("Something went wrong...");
        console.dir(err);
        return;
      }
      console.log(chalk.blue(data));
    },
  );

  console.log("----------------------------------------");
  console.log(chalk.blue(`Name: ${chalk.bold(packageData.name)}`));
  console.log(chalk.blue(`Version: ${chalk.bold(packageData.version)}`));
  console.log(chalk.blue(`Author: ${chalk.bold(packageData.author)}`));
  console.log(
    chalk.blue(`Description: ${chalk.bold(packageData.description)}`),
  );
  console.log(chalk.blue(`License: ${chalk.bold(packageData.license)}`));
  console.log(
    chalk.blue(`Repository: ${chalk.bold(packageData.repository.url)}`),
  );
  console.log("----------------------------------------");

  runServer(client);

  for (const file of functions) {
    const module = await import(`./functions/${file}`);
    module.default(client);
  }

  client.handleEvents(eventFiles, "./src/events");
  client.handleCommands(commandFolders, "./src/commands");
  client.login(process.env.TOKEN);
})();

process.on("unhandledRejection", async (error) => {
  await errorWebhook.send({
    embeds: [
      {
        title: "Unhandled Rejection",
        description: `\`\`\`js\n${error}\`\`\``,
        color: 0xff6961,
      },
    ],
  });

  console.error(chalk.red(error));
});

process.on("uncaughtException", async (error) => {
  await errorWebhook.send({
    embeds: [
      {
        title: "Uncaught Exception",
        description: `\`\`\`js\n${error}\`\`\``,
        color: 0xff6961,
      },
    ],
  });

  console.error(chalk.red(error));
});

process.on("warning", async (warning) => {
  await errorWebhook.send({
    embeds: [
      {
        title: "Warning",
        description: `\`\`\`js\n${warning}\`\`\``,
        color: 0xff6961,
      },
    ],
  });

  console.warn(chalk.yellow(warning));
});
