import { SlashCommandBuilder } from "discord.js";

const data = new SlashCommandBuilder()
    .setName("bored")
    .setDescription("Get a random activity to do")
    .setIntegrationTypes(0, 1)
    .setContexts(0, 1, 2);

const execute = async function (interaction) {
    const response = await fetch("https://bored-api.appbrewery.com/random");
    const data = await response.json();

    await interaction.reply({
        embeds: [
            {
                title: data.activity,
                description: data.type,
                color: 0x56b3fa
            }
        ]
    });
}
