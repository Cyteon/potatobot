import chalk from "chalk";
import { WebhookClient } from "discord.js";

const errorWebhook = new WebhookClient({
  url: process.env.ERROR_WEBHOOK,
});

export default {
  name: "error",
  async execute(err) {
    await errorWebhook.send({
      embeds: [
        {
          title: "Error",
          description: `\`\`\`js\n${err}\`\`\``,
          color: 0xff6961,
        },
      ],
    });
  },
};
