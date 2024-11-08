import { SlashCommandBuilder } from "discord.js";

const data = new SlashCommandBuilder()
    .setName("define")
    .setDescription("Defines the given word.")
    .setIntegrationTypes(0, 1)
    .setContexts(0, 1, 2)
    .addSubcommand((subcommand) =>
        subcommand
            .setName("dictionary")
            .setDescription("Get the definition of the word from the dictionary.")
            .addStringOption((option) =>
                option
                    .setName("word")
                    .setDescription("The word to define.")
                    .setRequired(true),
            ),
    )
    .addSubcommand((subcommand) =>
        subcommand
            .setName("urban")
            .setDescription("Get the definition of the word from the urban dictionary.")
            .addStringOption((option) =>
                option
                    .setName("word")
                    .setDescription("The word to define.")
                    .setRequired(true),
            )
    )


const execute = async function (interaction) {
    const subcommand = interaction.options.getSubcommand();
    const word = interaction.options.getString("word");

    if (subcommand === "dictionary") {
        const res = await fetch(`https://api.dictionaryapi.dev/api/v2/entries/en/${word}`);

        if (res.status === 404) {
            return await interaction.reply("Word not found.");
        }

        const data = (await res.json())[0]

        const embed = {
            title: data.word,
            description: data.meanings.reduce((acc, meaning) => {
                acc += `**${meaning.partOfSpeech}**\n`;
                acc += meaning.definitions.reduce((acc, definition, index) => {
                    acc += `${index + 1}. ${definition.definition}\n`;
                    return acc;
                }, "");
                return acc;
            }, "").slice(0, 2048),
            color: 0x56b3fa,
        };

        await interaction.reply({ embeds: [embed] });
    } else if (subcommand === "urban") {
        const res = await fetch(`https://api.urbandictionary.com/v0/define?term=${word}`);
        const data = await res.json();

        if (data.list.length === 0) {
            return await interaction.reply("Word not found.");
        }

        const definition = data.list[0];

        const embed = {
            title: definition.word,
            description: "||" + definition.definition + "||",
            color: 0x56b3fa,
            fields: [
                {
                    name: "📘 Example",
                    value: "||" + definition.example + "||"
                },
                {
                    name: "✍️ Author",
                    value: definition.author,
                },
                {
                    name: "👍 Upvotes", 
                    value: definition.thumbs_up,
                    inline: true,
                },
                {
                    name: "👎 Downvotes",
                    value: definition.thumbs_down,
                    inline: true,
                },
            ],
            footer: {
                text: "⚠️ Urban Dictionary definitions may contain explicit content."
            }
        };

        await interaction.reply({ embeds: [embed] });
    }
}

export default { data, execute };