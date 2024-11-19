import {
  ActionRowBuilder,
  ButtonBuilder,
  ButtonStyle,
  SlashCommandBuilder,
} from "discord.js";

const data = new SlashCommandBuilder()
  .setName("search")
  .setDescription("Search with an Engine")
  .setIntegrationTypes(0, 1)
  .setContexts(0, 1, 2)
  .addStringOption((input) =>
    input
      .setName("engine")
      .setDescription("The engine to search with")
      .setRequired(true)
      .addChoices(
        {
          name: "Reddit",
          value: "reddit",
        },
        {
          name: "Qwant",
          value: "qwant",
        },
      ),
  )
  .addStringOption((input) =>
    input
      .setName("query")
      .setDescription("The query to search for")
      .setRequired(true),
  );

const execute = async function (interaction) {
  const engine = interaction.options.getString("engine");
  const query = interaction.options.getString("query");

  if (engine === "reddit") {
    const response = await fetch(
      `https://www.reddit.com/search/.json?q=${query}`,
    );

    if (!response.ok) {
      return interaction.reply({
        content: `Failed to search Reddit: ${response.statusText}`,
      });
    }

    const json = await response.json();

    const posts = json.data.children.slice(0, 10).map((post) => {
      if (post.data.over_18) {
        return;
      }

      return {
        title: post.data.title,
        text: post.data.selftext,
        subreddit: post.data.subreddit,
        author: post.data.author,
        url: post.data.url,
        ups: post.data.ups,
      };
    });

    let current = 0;

    let embed = {
      title: posts[0].title,
      description: `${posts[0].text.slice(0, 400)}${posts[0].text.length > 400 ? "..." : ""}`,
      url: posts[0].url,
      color: 0xff4500,
      footer: {
        text: `👍 ${posts[0].ups} | r/${posts[0].subreddit} | u/${posts[0].author} | ${current + 1}/${posts.length}`,
      },
    };

    const backButton = new ButtonBuilder()
      .setCustomId(`back-${interaction.id}`)
      .setLabel("Back")
      .setStyle(ButtonStyle.Secondary);

    const nextButton = new ButtonBuilder()
      .setCustomId(`next-${interaction.id}`)
      .setLabel("Next")
      .setStyle(ButtonStyle.Secondary);

    const row = new ActionRowBuilder().addComponents(backButton, nextButton);

    const msg = await interaction.reply({
      embeds: [embed],
      components: [row],
    });

    const filter = (i) => i.user.id === interaction.user.id;

    const collector = msg.createMessageComponentCollector({
      filter,
    });

    collector.on("collect", async (i) => {
      if (i.customId === `back-${interaction.id}`) {
        current--;

        if (current < 0) {
          current = posts.length - 1;
        }
      } else if (i.customId === `next-${interaction.id}`) {
        current++;

        if (current >= posts.length) {
          current = 0;
        }
      }

      embed = {
        title: posts[current].title,
        description: `${posts[current].text.slice(0, 397)}${posts[current].text.length > 400 ? "..." : ""}`,
        url: posts[current].url,
        color: 0xff4500,
        footer: {
          text: `👍 ${posts[current].ups} | r/${posts[current].subreddit} | u/${posts[current].author} | ${current + 1}/${posts.length}`,
        },
      };

      await i.update({
        embeds: [embed],
      });
    });
  } else if (engine === "qwant") {
    let current = 0;

    const response = await fetch(
      `https://api.qwant.com/v3/search/web?q=${query}&count=10&locale=en_us`,
    );

    if (!response.ok) {
      return interaction.reply({
        content: `Failed to search Qwant: ${response.statusText}`,
      });
    }

    const json = await response.json();

    let mainline = 0;

    for (let i = 0; i < json.data.result.items.mainline.length; i++) {
      if (json.data.result.items.mainline[i].type === "web") {
        mainline = i;
        break;
      }
    }

    const results = json.data.result.items.mainline[mainline].items.map(
      (result) => {
        return {
          title: result.title,
          url: result.url,
          desc: result.desc || "No description",
        };
      },
    );

    let embed = {
      title:
        results[current].title.length > 256
          ? results[current].title.slice(0, 253) + "..."
          : results[current].title,
      url: results[current].url.length > 2000 ? "" : results[current].url,
      description:
        results[current].desc.length > 400
          ? results[current].desc.slice(0, 397) + "..."
          : results[current].desc,
      color: 0x56b3fa,
      footer: {
        text: `${current + 1}/${results.length}`,
      },
    };

    const backButton = new ButtonBuilder()
      .setCustomId(`back-${interaction.id}`)
      .setLabel("Back")
      .setStyle(ButtonStyle.Secondary);

    const nextButton = new ButtonBuilder()
      .setCustomId(`next-${interaction.id}`)
      .setLabel("Next")
      .setStyle(ButtonStyle.Secondary);

    const row = new ActionRowBuilder().addComponents(backButton, nextButton);

    const msg = await interaction.reply({
      embeds: [embed],
      components: [row],
    });

    const filter = (i) => i.user.id === interaction.user.id;

    const collector = msg.createMessageComponentCollector({
      filter,
    });

    collector.on("collect", async (i) => {
      if (i.customId === `back-${interaction.id}`) {
        current--;

        if (current < 0) {
          current = results.length - 1;
        }
      } else if (i.customId === `next-${interaction.id}`) {
        current++;

        if (current >= results.length) {
          current = 0;
        }
      }

      embed = {
        title:
          results[current].title.length > 256
            ? results[current].title.slice(0, 253) + "..."
            : results[current].title,
        url: results[current].url.length > 2000 ? "" : results[current].url,
        description:
          results[current].desc.length > 400
            ? results[current].desc.slice(0, 397) + "..."
            : results[current].desc,
        color: 0x56b3fa,
        footer: {
          text: `${current + 1}/${results.length}`,
        },
      };

      await i.update({
        embeds: [embed],
      });
    });
  }
};

export default { data, execute };
