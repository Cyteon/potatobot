import { SlashCommandSubcommandBuilder } from "discord.js";
import EconomyUser from "../../../lib/models/EconomyUser.js";

const data = new SlashCommandSubcommandBuilder()
    .setName("balance")
    .setDescription("Check your balance!")

const execute = async function (interaction) {
    let user = await EconomyUser.findOne({ id: interaction.user.id }).cache("1 minute");

    if (!user) {
        user = await EconomyUser.create({
            id: interaction.user.id,
            balance: 50
        });
    }

    await interaction.reply(`💵 You have $${user.balance}`);
}

export default { data, execute };