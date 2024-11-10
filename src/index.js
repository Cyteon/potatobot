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
import { Connectors } from "shoukaku";
import { Kazagumo } from "kazagumo";
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

const Nodes = [
  {
    name: process.env.LAVALINK_NAME,
    url: process.env.LAVALINK_HOST + ":" + process.env.LAVALINK_PORT,
    auth: process.env.LAVALINK_PASSWORD,
    secure: true,
  },
];

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
    GatewayIntentBits.GuildModeration,
    GatewayIntentBits.GuildVoiceStates,
  ],
});

const kazagumo = new Kazagumo(
  {
    defaultSearchEngine: "youtube",
    send: (guildId, payload) => {
      const guild = client.guilds.cache.get(guildId);
      if (guild) guild.shard.send(payload);
    },
  },
  new Connectors.DiscordJS(client),
  Nodes,
);
client.kazagumo = kazagumo;

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
        title: "Heartbreak :( (Unhandled Rejection)",
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

// Music

kazagumo.shoukaku.on("ready", (name) => {
  console.log(chalk.green(`Shoukaku Node: ${name} | Connected!`));
});

kazagumo.shoukaku.on("error", async (name, error) => {
  if (error.errors) {
    console.error(
      chalk.red(`Shoukaku Node: ${name} | Error: ${error.errors.join("\n")}`),
    );

    await errorWebhook.send({
      embeds: [
        {
          title: "Shoukaku Error",
          description: `Node: ${name}\n\`\`\`${error.errors.join("\n")}\`\`\``,
          color: 0xff6961,
        },
      ],
    });
  } else {
    console.error(chalk.red(`Shoukaku Node: ${name} | Error: ${error}`));

    await errorWebhook.send({
      embeds: [
        {
          title: "Shoukaku Error",
          description: `Node: ${name}\n\`\`\`Error: ${error}\`\`\``,
          color: 0xff6961,
        },
      ],
    });
  }
});

kazagumo.shoukaku.on("disconnect", (name, count) => {
  const players = [...kazagumo.shoukaku.players.values()].filter(
    (p) => p.node.name === name,
  );
  players.map((player) => {
    kazagumo.destroyPlayer(player.guildId);
    player.destroy();
  });
  console.warn(`Lavalink ${name}: Disconnected`);
});

kazagumo.on("playerStart", (player, track) => {
  client.channels.cache
    .get(player.textId)
    ?.send({ content: `Now playing **${track.title}** by **${track.author}**` })
    .then((x) => player.data.set("message", x));
});

kazagumo.on("playerEnd", (player) => {
  player.data.get("message")?.edit({ content: `Finished playing` });
});

kazagumo.on("playerEmpty", (player) => {
  client.channels.cache
    .get(player.textId)
    ?.send({ content: `Destroyed player due to inactivity.` })
    .then((x) => player.data.set("message", x));
  player.destroy();
});
