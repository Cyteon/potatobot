import { SlashCommandBuilder } from "discord.js";
import OpenAI from "openai";
import AiConvo from "../../lib/models/AiConvo.js";

let lastApiKey = 0;
function getClient() {
  const apiKeyCount = process.env.GROQ_API_KEY_COUNT;

  lastApiKey = lastApiKey + 1;

  if (lastApiKey > apiKeyCount) {
    lastApiKey = 1;
  }

  return new OpenAI({
    apiKey: process.env[`GROQ_API_KEY_${lastApiKey}`],
    baseURL: "https://api.groq.com/openai/v1",
  });
}

const replaceList = [
  {
    old: "@everyone",
    new: "@​everyone",
  },
  {
    old: "@here",
    new: "@​here",
  },
  {
    old: "<@",
    new: "<@​",
  },
  {
    old: "discord.gg",
    new: "[filtered]",
  },
  {
    old: "discord.com/invite",
    new: "[filtered]",
  },
];

const models = [
  "llama-3.2-11b-text-preview",
  "llama-3.1-70b-versatile",
  "llama-3.1-8b-instant",
  "llama3-groq-70b-8192-tool-use-preview",
  "llama3-groq-8b-8192-tool-use-preview",
  "gemma2-9b-it",
];

const data = new SlashCommandBuilder()
  .setName("ai")
  .setDescription("Talk to the AI")
  .setIntegrationTypes(0, 1)
  .setContexts(0, 1, 2)
  .addStringOption((input) =>
    input
      .setName("message")
      .setDescription("The message to send to the AI")
      .setRequired(true),
  );

const execute = async function (interaction) {
  await interaction.deferReply();

  const message = interaction.options.getString("message");

  let convo = await AiConvo.findOne({
    isChannel: false,
    id: interaction.user.id,
  });

  const client = getClient();

  if (!convo) {
    convo = new AiConvo({
      isChannel: false,
      id: interaction.user.id,
      messages: [],
      expiresAt:
        new Date(Date.now() + 1000 * 60 * 60 * 24 * 7).valueOf() / 1000,
    });
  }

  convo.messageArray.push({
    role: "user",
    content: message,
  });

  let aiResponse = "";

  for (const model of models) {
    try {
      const response = await client.chat.completions.create({
        model: model,
        messages: convo.messageArray.map((message) => ({
          role: message.role,
          content: message.content,
        })),
        stream: false,
      });

      aiResponse = response.choices[0].message.content;
      break;
    } catch (error) {
      aiResponse = "An error occurred while talking to the AI.";
    }
  }

  convo.messageArray.push({
    role: "assistant",
    content: aiResponse,
  });

  convo.save();

  for (const replace of replaceList) {
    aiResponse = aiResponse.replace(replace.old, replace.new);
  }

  if (aiResponse.length > 2000) {
    const file = Buffer.from(aiResponse, "utf-8");

    await interaction.editReply({
      content: "The response was too long, so here's a file instead.",
      files: [
        {
          attachment: file,
          name: "ai-response.txt",
        },
      ],
    });
  } else {
    await interaction.editReply(aiResponse);
  }
};

export default { data, execute };
