import {
  SlashCommandBuilder,
  EmbedBuilder,
  ButtonBuilder,
  ActionRowBuilder,
  ButtonStyle,
} from "discord.js";

const data = new SlashCommandBuilder()
  .setName("github")
  .setDescription("Returns data from GitHub.")
  .addSubcommand((subcommand) =>
    subcommand
    .setName("user")
    .setDescription("Gets a GitHub profile via their username.")
    .addStringOption((input) =>
        input
          .setName("username")
          .setDescription("...")
          .setRequired(true)
      )
  )
  .addSubcommand((subcommand) =>
    subcommand
      .setName("repo")
      .setDescription("Searches for the specified GitHub repo.")
      .addStringOption((input) =>
        input
          .setName("owner")
          .setDescription("...")
          .setRequired(true)
      )
      .addStringOption((input) =>
        input
          .setName("repo")
          .setDescription("...")
          .setRequired(true)
      )
);

const execute = async function (interaction) {
    const { options } = interaction;
    const subCommand = options.getSubcommand();

    if (subCommand === "user") {
      try {
        const user = options.getString("username")
        const response = await fetch(`https://api.github.com/users/${user}`);
        const userData = await response.json();

        if (response.status !== 200) {
          return await interaction.reply("User not found!");
        }

        const embed = new EmbedBuilder()
          .setTitle(`GitHub Profile: ${userData.login}`)
          .setDescription(`**Bio:** ${userData.bio}`)
          .setColor(0xFFFFFF)
          .setThumbnail(userData.avatar_url)
          .addFields({ name: "Username 📛: ", value: userData.name, inline: true })
          .addFields({ name: "Repos 📁: ", value: userData.public_repos.toLocaleString('en-US'), inline: true })
          .addFields({ name: "Location 📍: ", value: userData.location, inline: true })
          .addFields({ name: "Company 🏢: ", value: userData.company, inline: true })
          .addFields({ name: "Followers 👥: ", value: userData.followers.toLocaleString('en-US'), inline: true })
          .addFields({ name: "Website 🖥️: ", value: userData.blog, inline: true })

        const profileButton = new ButtonBuilder()
          .setLabel("GitHub Profile")
          .setStyle(ButtonStyle.Link)
          .setURL(userData.html_url);

        const row = new ActionRowBuilder()
          .addComponents(profileButton);

        return await interaction.reply({ embeds: [embed], components: [row] });
      } catch (error) {
        console.error(error);
      }
    } else if (subCommand === "repo") {
      try {
        const owner = options.getString("owner");
        const repo = options.getString("repo");
        const response = await fetch(`https://api.github.com/repos/${owner}/${repo}`);
        const repoData = await response.json();

        if (response.status !== 200) {
          return await interaction.reply("Repo not found!");
        }

        const embed = new EmbedBuilder()
          .setTitle(`GitHub Repository: ${repoData.name}`)
          .setDescription(`**Description:** ${repoData.description}`)
          .setColor(0xFFFFFF)
          .setThumbnail(repoData.owner.avatar_url)
          .addFields({ name: "Author 🖊:", value: `__${repoData.owner.login}__`, inline: true })
          .addFields({ name: "Stars ⭐:", value: repoData.stargazers_count.toLocaleString('en-US'), inline: true })
          .addFields({ name: "Forks 🍴:", value: repoData.forks_count.toLocaleString('en-US'), inline: true })
          .addFields({ name: "Language 💻:", value: repoData.language, inline: true })
          .addFields({ name: "Size 🗃️:", value: `${(repoData.size / 1000).toFixed(2)} MB`, inline: true });

        if (repoData.license) {
          embed.addFields({ name: "License name 📃:", value: repoData.license.name, inline: true });
        } else {
          embed.addFields({ name: "License name 📃:", value: "This Repo doesn't have a license", inline: true });
        }

        const repoButton = new ButtonBuilder()
          .setLabel("GitHub Repository")
          .setStyle(ButtonStyle.Link)
          .setURL(repoData.html_url);

        const row = new ActionRowBuilder()
          .addComponents(repoButton);

        return await interaction.reply({ embeds: [embed], components: [row] });
      } catch (error) {
        console.error(error);
      }
    }
};

export default { data, execute };
