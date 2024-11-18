import { SlashCommandBuilder, AttachmentBuilder } from "discord.js";
import { createCanvas } from "canvas";
import Color from "color";

const data = new SlashCommandBuilder()
  .setName("color")
  .setDescription("Get info about a color")
  .setIntegrationTypes(0, 1)
  .setContexts(0, 1, 2)
  .addStringOption((option) =>
    option
      .setName("color")
      .setDescription("The color to get info about")
      .setRequired(true),
  );

const execute = async function (interaction) {
  const color = interaction.options.getString("color").replace("0x", "#");

  const canvas = createCanvas(100, 100);
  const ctx = canvas.getContext("2d");

  ctx.fillStyle = color;
  ctx.fillRect(0, 0, 100, 100);

  const image = canvas.toBuffer();
  const attachment = new AttachmentBuilder(image, { name: "color.png" });

  const parsed = Color(color);

  await interaction.reply({
    embeds: [
      {
        title: color,
        color: parsed
          .rgb()
          .array()
          .reduce((acc, val) => (acc << 8) | val),
        description: `
        RGB: **${parsed.rgb().array().join(", ")}**
        Hex: **${parsed.hex()}**
        HSL: **${parsed.hsl().array().join(", ")}**
        Luminance: **${parsed.luminosity()}**`,
        /*image: {
          url: `attachment://color.png`,
        },*/ // Removed since it was always black (broken)
      },
    ],
    // files: [attachment],
  });
};

export default { data, execute };
