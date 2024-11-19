import { SlashCommandBuilder } from "discord.js";

const data = new SlashCommandBuilder()
    .setName("translate")
    .setDescription("Translate text")
    .setIntegrationTypes(0, 1)
    .setContexts(0, 1, 2)
    .addStringOption((input) =>
        input.setName("text")
            .setDescription("The text to translate")
            .setRequired(true)
    )
    .addStringOption((input) =>
        input.setName("to")
            .setDescription("The language to translate to")
    )

const execute = async function (interaction) {
    const text = interaction.options.getString("text");
    const to = interaction.options.getString("to") || "en";

    const response = await fetch(
        `https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=${to}&dt=t&q=${encodeURIComponent(text)}`,
    );

    if (!response.ok) {
        return interaction.reply({
            content: `Failed to translate text: ${response.statusText}`,
        });
    }

    const json = await response.json();

    return interaction.reply({
        embeds: [
            {
                title: "Translation",
                fields: [
                    {
                        name: "Input",
                        value: `\`\`\`\n${text}\n\`\`\``
                    },
                    {
                        name: "Output",
                        value: `\`\`\`\n${json[0][0][0]}\n\`\`\``
                    }
                ],
                color: 0x56b3fa
            }
        ]
    });
}

export default { data, execute };