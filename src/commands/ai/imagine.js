import { SlashCommandBuilder, AttachmentBuilder } from "discord.js";
import { RateLimiter } from "discord.js-rate-limiter";
import random from "random";

let rateLimiter = new RateLimiter(1, 5000);

const data = new SlashCommandBuilder()
  .setName("imagine")
  .setDescription("Imagine something")
  .setIntegrationTypes(0, 1)
  .setContexts(0, 1, 2)
  .addStringOption((str) =>
    str
      .setName("model")
      .setDescription("The model to use")
      .setRequired(true)
      .addChoices(
        {
          name: "FLUX.1 Schnell",
          value: "@cf/black-forest-labs/flux-1-schnell",
        },
        {
          name: "Stable Diffusion XL Lightning",
          value: "@cf/bytedance/stable-diffusion-xl-lightning",
        },
        {
          name: "Stable Diffusion XL Base",
          value: "@cf/stabilityai/stable-diffusion-xl-base-1.0",
        },
      ),
  )
  .addStringOption((str) =>
    str.setName("prompt").setDescription("The prompt to use").setRequired(true),
  );

const execute = async function (interaction) {
  let limited = rateLimiter.take(interaction.user.id);

  if (limited) {
    return await interaction.reply({
      content: "🕒 Please wait a few seconds before using this command again.",
    });
  }

  await interaction.reply({
    content: "🎨 Imagining...",
  });

  const model = interaction.options.getString("model");
  const prompt = interaction.options.getString("prompt");

  let body = {
    prompt,
    seed: random.int(0, 1000000),
  };

  if (model === "@cf/black-forest-labs/flux-1-schnell") {
    body["num_steps"] = 8;
  }

  const response = await fetch(
    `https://api.cloudflare.com/client/v4/accounts/${process.env.CF_ACCOUNT_ID}/ai/run/${model}`,
    {
      headers: {
        Authorization: `Bearer ${process.env.CF_WORKERS_AI_API_TOKEN}`,
      },
      method: "POST",
      body: JSON.stringify(body),
    },
  );

  if (response.ok) {
    // Some models have diffrent response types
    if (model === "@cf/black-forest-labs/flux-1-schnell") {
      const data = await response.json();

      const base64 = data.result.image;

      const attach = new AttachmentBuilder(
        Buffer.from(base64, "base64"),
        "imagine.png",
      );

      await interaction.editReply({
        content: "🎨 Here's what I imagined",
        files: [attach],
      });
    } else if (
      // Models providing raw image as response
      model === "@cf/bytedance/stable-diffusion-xl-lightning" ||
      model === "@cf/stabilityai/stable-diffusion-xl-base-1.0"
    ) {
      const buffer = Buffer.from(await response.arrayBuffer());

      const attach = new AttachmentBuilder(buffer, "imagine.png");

      await interaction.editReply({
        content: "🎨 Here's what I imagined",
        files: [attach],
      });
    }
  } else {
    const data = await response.json();

    await interaction.editReply({
      content: `⚠️ ${data.errors[0].message}`,
      ephemeral: true,
    });

    console.error(data);
  }
};

export default { data, execute };
