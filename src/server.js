import express from "express";
import chalk from "chalk";
const app = express();

const port = process.env.PORT || 3000;

export default function runServer(bot) {
  console.log(chalk.yellow("Starting server..."));

  app.get("/", (req, res) => {
    let command_count = 0;

    bot.commands.forEach((command) => {
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

    res.json({
      username: bot.user.username,
      users: bot.guilds.cache.reduce((a, g) => a + g.memberCount, 0),
      guilds: bot.guilds.cache.size,
      shards: bot.ws.shards.size,
      commandCount: command_count,
      uptime: process.uptime(),
    });
  });

  app.listen(port, () => {
    console.log(chalk.green(`Server is running on http://localhost:${port}`));
  });
}
