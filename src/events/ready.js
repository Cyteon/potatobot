import chalk from "chalk";

export default {
  name: "ready",
  once: true,
  async execute(client) {
    console.log(chalk.green("Logged in as " + chalk.bold(client.user.tag)));
  },
};
