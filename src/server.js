import express from "express";
import chalk from "chalk";
const app = express();

const port = process.env.PORT || 3000;

export default function runServer(bot) {
  app.get("/", (req, res) => {
    res.send(`${bot.user.username} is online!`);
  });

  app.listen(port, () => {
    console.log(chalk.green(`Server is running on port ${port}`));
  });
}
