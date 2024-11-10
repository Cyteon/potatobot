import { SlashCommandBuilder, AttachmentBuilder } from "discord.js";

const data = new SlashCommandBuilder()
  .setName("avatar")
  .setDescription("Commands related to user avatars")
  .setIntegrationTypes(0, 1)
  .setContexts(0, 1, 2)
  .addStringOption((input) =>
    input
      .setName("action")
      .setDescription("What do with the avatar")
      .setRequired(true)
      .addChoices(
        {
          name: "🔍 View | user",
          value: "view",
        },
        {
          name: "👀 Blur | user",
          value: "blur",
        },
        {
          name: "👀 Pixelate | user",
          value: "pixelate",
        },
        {
          name: "😠 Trigger | user",
          value: "trigger",
        },
        {
          name: "🔒 Jail | user",
          value: "jail",
        },
        {
          name: "🔥 Wasted | user",
          value: "wasted",
        },
        {
          name: "✅ Passed | user",
          value: "passed",
        },
        {
          name: "🔁 Tweet | text",
          value: "tweet",
        },
        {
          name: "🎥 Youtube Comment | text",
          value: "youtube",
        },
      ),
  )
  .addUserOption((input) =>
    input.setName("user").setDescription("The user to get the avatar for"),
  )
  .addStringOption((input) =>
    input
      .setName("text")
      .setDescription("The text to use for the tweet or youtube comment"),
  );

const execute = async function (interaction) {
  const action = interaction.options.getString("action");
  const user = interaction.options.getUser("user") || interaction.user;
  const text = interaction.options.getString("text") || "";

  const avatar = user
    .displayAvatarURL({ format: "png" })
    .replace(/.webp/g, ".png");

  if (action == "view") {
    return interaction.reply({
      content: avatar,
    });
  } else if (action == "blur") {
    const image = await fetch(
      `https://some-random-api.com/canvas/misc/blur?avatar=${avatar}`,
    );

    return interaction.reply({
      files: [
        new AttachmentBuilder(Buffer.from(await image.arrayBuffer()), {
          name: "blurred.png",
        }),
      ],
    });
  } else if (action == "pixelate") {
    const image = await fetch(
      `https://some-random-api.com/canvas/misc/pixelate?avatar=${avatar}`,
    );

    return interaction.reply({
      files: [
        new AttachmentBuilder(Buffer.from(await image.arrayBuffer()), {
          name: "pixelated.png",
        }),
      ],
    });
  } else if (action == "trigger") {
    const image = await fetch(
      `https://some-random-api.com/canvas/overlay/triggered?avatar=${avatar}`,
    );

    return interaction.reply({
      files: [
        new AttachmentBuilder(Buffer.from(await image.arrayBuffer()), {
          name: "triggered.gif",
        }),
      ],
    });
  } else if (action == "jail") {
    const image = await fetch(
      `https://some-random-api.com/canvas/overlay/jail?avatar=${avatar}`,
    );

    return interaction.reply({
      files: [
        new AttachmentBuilder(Buffer.from(await image.arrayBuffer()), {
          name: "jailed.png",
        }),
      ],
    });
  } else if (action == "wasted") {
    const image = await fetch(
      `https://some-random-api.com/canvas/overlay/wasted?avatar=${avatar}`,
    );

    return interaction.reply({
      files: [
        new AttachmentBuilder(Buffer.from(await image.arrayBuffer()), {
          name: "jailed.png",
        }),
      ],
    });
  } else if (action == "passed") {
    const image = await fetch(
      `https://some-random-api.com/canvas/overlay/passed?avatar=${avatar}`,
    );

    return interaction.reply({
      files: [
        new AttachmentBuilder(Buffer.from(await image.arrayBuffer()), {
          name: "jailed.png",
        }),
      ],
    });
  } else if (action == "tweet") {
    const image = await fetch(
      `https://some-random-api.com/canvas/misc/tweet?avatar=${avatar}&username=${user.username}&displayname=${user.username}&comment=${text}`,
    );

    return interaction.reply({
      files: [
        new AttachmentBuilder(Buffer.from(await image.arrayBuffer()), {
          name: "tweet.png",
        }),
      ],
    });
  } else if (action == "youtube") {
    const image = await fetch(
      `https://some-random-api.com/canvas/misc/youtube-comment?avatar=${avatar}&username=${user.username}&comment=${text}`,
    );

    return interaction.reply({
      files: [
        new AttachmentBuilder(Buffer.from(await image.arrayBuffer()), {
          name: "youtube.png",
        }),
      ],
    });
  }
};

export default { data, execute };
