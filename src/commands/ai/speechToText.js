import { SlashCommandBuilder } from "discord.js";

const data = new SlashCommandBuilder()
  .setName("speech-to-text")
  .setDescription("Convert speech to text")
  .setIntegrationTypes(0, 1)
  .setContexts(0, 1, 2)
  .addAttachmentOption((input) =>
    input
      .setName("audio")
      .setDescription("The audio file to convert to text")
      .setRequired(true),
  );

const execute = async function (interaction) {
  await interaction.deferReply();

  const attachment = interaction.options.get("audio").attachment;

  if (
    !attachment.name.endsWith(".mp3") &&
    !attachment.name.endsWith(".wav") &&
    !attachment.name.endsWith(".ogg") &&
    !attachment.name.endsWith(".flac")
  ) {
    return await interaction.editReply({
      content: ":x: Only MP3, WAV, OGG, and FLAC files are supported.",
    });
  }

  const attachmentRes = await fetch(attachment.attachment);
  const audio = await attachmentRes.arrayBuffer();

  const response = await fetch(
    `https://api.cloudflare.com/client/v4/accounts/${process.env.CF_ACCOUNT_ID}/ai/run/@cf/openai/whisper`,
    {
      headers: {
        Authorization: `Bearer ${process.env.CF_WORKERS_AI_API_TOKEN}`,
      },
      method: "POST",
      body: audio,
    },
  );

  if (!response.ok) {
    console.error(await response.text());

    return await interaction.editReply({
      content: ":x: Failed to convert speech to text.",
    });
  }

  const data = await response.json();

  if (data.result.text > 2000) {
    await interaction.editReply({
      content: "🎤 Here's the transcript",
      files: [
        {
          name: "transcript.txt",
          content: data.result.text,
        },
      ],
    });
  } else {
    await interaction.editReply({
      content: "🎤 Here's the transcript",
      embeds: [
        {
          description: data.result.text,
        },
      ],
    });
  }
};

export default { data, execute };
