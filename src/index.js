/*
  Repository: https://github.com/cyteon/potatobot
  License: GPL-3.0
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
