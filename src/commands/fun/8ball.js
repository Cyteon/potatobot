import { SlashCommandBuilder } from "discord.js";
import random from "random";

const data = new SlashCommandBuilder()
    .setName("8ball")
    .setDescription("Ask the 8ball a question")
    .setIntegrationTypes(0, 1)
    .setContexts(0, 1, 2)
    .addStringOption((option) =>
        option
            .setName("question")
            .setDescription("The question to ask the 8ball")
            .setRequired(true),
    );

const execute = async function (interaction) {
    const choices = [
        "It is certain.",
        "It is decidedly so.",
        "Yes.",
        "Without a doubt.",
        "Yes – definitely.",
        "You may rely on it.",
        "As I see it, yes.",
        "No",
        "Ask again later.",
        "Better not tell you now.",
        "Cannot predict now.",
        "Concentrate and ask again.",
        "Don't count on it.",
        "My reply is no.",
        "My sources say no.",
        "Never"
    ];

    const choice = random.choice(choices);

    await interaction.reply(choice);
}

export default { data, execute };