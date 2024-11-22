import {
  SlashCommandSubcommandBuilder,
  EmbedBuilder,
  ButtonBuilder,
  ButtonStyle,
  ActionRowBuilder,
} from "discord.js";

const data = new SlashCommandSubcommandBuilder()
  .setName("user")
  .setDescription("Gets a GitHub profile via their username.")
  .addStringOption((input) =>
    input.setName("username").setDescription("...").setRequired(true),
  );

const execute = async function (interaction) {
  try {
    const user = interaction.options.getString("username");
    const response = await fetch(`https://api.github.com/users/${user}`);
    const userData = await response.json();

    if (response.status !== 200) {
      return await interaction.reply("User not found!");
    }

    const embed = new EmbedBuilder()
      .setTitle(`GitHub Profile: ${userData.login}`)
      .setDescription(`**Bio:** ${userData.bio}`)
      .setColor(0xffffff)
      .setThumbnail(userData.avatar_url)
      .addFields({
        name: "Username 📛: ",
        value: userData.name,
        inline: true,
      })
      .addFields({
        name: "Repos 📁: ",
        value: userData.public_repos.toLocaleString("en-US"),
        inline: true,
      })
      .addFields({
        name: "Location 📍: ",
        value: userData.location || "N/A",
        inline: true,
      })
      .addFields({
        name: "Company 🏢: ",
        value: userData.company || "N/A",
        inline: true,
      })
      .addFields({
        name: "Followers 👥: ",
        value: userData.followers.toLocaleString("en-US"),
        inline: true,
      })
      .addFields({
        name: "Website 🌐: ",
        value: userData.blog || "N/A",
        inline: true,
      });

    const profileButton = new ButtonBuilder()
      .setLabel("GitHub Profile")
      .setStyle(ButtonStyle.Link)
      .setURL(userData.html_url);

    const row = new ActionRowBuilder().addComponents(profileButton);

    return await interaction.reply({ embeds: [embed], components: [row] });
  } catch (error) {
    console.error(error);
  }
};

export default { data, execute };
