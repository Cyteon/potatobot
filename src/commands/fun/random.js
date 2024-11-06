import { SlashCommandBuilder } from "@discordjs/builders";

const data = new SlashCommandBuilder()
  .setName("random")
  .setDescription("Gets a random image of something.")
  .addSubcommand((subcommand) =>
    subcommand.setName("bird").setDescription("Get a random bird image"),
  )
  .addSubcommand((subcommand) =>
    subcommand
      .setName("boykisser")
      .setDescription("Get a random boykisser image"),
  )
  .addSubcommand((subcommand) =>
    subcommand.setName("cat").setDescription("Get a random cat image"),
  )
  .addSubcommand((subcommand) =>
    subcommand.setName("coffee").setDescription("Get a random coffee image"),
  )
  .addSubcommand((subcommand) =>
    subcommand.setName("dog").setDescription("Get a random dog image"),
  )
  .addSubcommand((subcommand) =>
    subcommand.setName("fox").setDescription("Get a random fox image"),
  )
  .addSubcommand((subcommand) =>
    subcommand.setName("gary").setDescription("Get a random gary image"),
  )
  .addSubcommand((subcommand) =>
    subcommand.setName("gary-joke").setDescription("Get a random gary joke"),
  )
  .addSubcommand((subcommand) =>
    subcommand.setName("gary-quote").setDescription("Get a random gary quote"),
  )
  .addSubcommand((subcommand) =>
    subcommand.setName("gayrate").setDescription("Get your gay rate"),
  )
  .addSubcommand((subcommand) =>
    subcommand
      .setName("kangaroo")
      .setDescription("Get a random kangaroo image"),
  )
  .addSubcommand((subcommand) =>
    subcommand.setName("koala").setDescription("Get a random koala image"),
  )
  .addSubcommand((subcommand) =>
    subcommand.setName("panda").setDescription("Get a random panda image"),
  )
  .addSubcommand((subcommand) =>
    subcommand.setName("raccoon").setDescription("Get a random raccoon image"),
  )
  .addSubcommand((subcommand) =>
    subcommand
      .setName("red-panda")
      .setDescription("Get a random red panda image"),
  );

const execute = async function (interaction) {
  const { options } = interaction;
  const subCommand = options.getSubcommand();

  const garyHeaders = {
    "Content-Type": "application/json",
    api_key: process.env.GARY_API_KEY,
  };

  if (subCommand === "bird") {
    const response = await fetch("https://some-random-api.com/animal/bird");
    const json = await response.json();
    const imgurl = json.image;

    await interaction.reply({ content: imgurl, ephemeral: false });
  } else if (subCommand === "boykisser") {
    const response = await fetch(
      "https://api.gizzy.is-a.dev/api/random?redirect=0",
    );
    const json = await response.json();
    const imgurl = json.url;

    await interaction.reply({ content: imgurl, ephemeral: false });
  } else if (subCommand === "cat") {
    const response = await fetch("https://some-random-api.com/animal/cat");
    const json = await response.json();
    const imgurl = json.image;

    await interaction.reply({ content: imgurl, ephemeral: false });
  } else if (subCommand === "coffee") {
    const response = await fetch("https://coffee.alexflipnote.dev/random.json");
    const json = await response.json();
    const imgurl = json.file;

    await interaction.reply({ content: imgurl, ephemeral: false });
  } else if (subCommand === "dog") {
    const response = await fetch("https://some-random-api.com/animal/dog");
    const json = await response.json();
    const imgurl = json.image;

    await interaction.reply({ content: imgurl, ephemeral: false });
  } else if (subCommand === "fox") {
    const response = await fetch("https://some-random-api.com/animal/fox");
    const json = await response.json();
    const imgurl = json.image;

    await interaction.reply({ content: imgurl, ephemeral: false });
  } else if (subCommand === "gary") {
    const response = await fetch("https://garybot.dev/api/gary", {
      method: "GET",
      headers: garyHeaders,
    });
    const json = await response.json();
    const imgurl = json.url;

    await interaction.reply({ content: imgurl, ephemeral: false });
  } else if (subCommand === "gary-joke") {
    const response = await fetch("https://garybot.dev/api/joke", {
      method: "GET",
      headers: garyHeaders,
    });
    const json = await response.json();
    const joke = json.joke;

    await interaction.reply({ content: joke, ephemeral: false });
  } else if (subCommand === "gary-quote") {
    const response = await fetch("https://garybot.dev/api/quote", {
      method: "GET",
      headers: garyHeaders,
    });
    const json = await response.json();
    const quote = json.quote;

    await interaction.reply({ content: quote, ephemeral: false });
  } else if (subCommand === "gayrate") {
    const emojis = [
      "😳",
      "😳",
      "😳",
      "😳",
      "😳",
      "😳",
      "😳",
      "😳",
      "😳",
      "😳",
      "🏳️‍🌈",
      "🔥",
    ];
    const percentage = Math.floor(Math.random() * 100) + 1;
    let emoji;

    if (percentage > 90) {
      emoji = "🌈";
    } else if (percentage < 10) {
      emoji = "🔥";
    } else {
      emoji = emojis[Math.floor(emojis.length * Math.random())];
    }

    await interaction.reply(`<@${user}> is ${percentage}% gay ${emoji}`);
  } else if (subCommand === "kangaroo") {
    const response = await fetch("https://some-random-api.com/animal/kangaroo");
    json = await response.json();
    imgurl = json.image;

    await interaction.reply({ content: imgurl, ephemeral: false });
  } else if (subCommand === "koala") {
    const response = await fetch("https://some-random-api.com/animal/koala");
    const json = await response.json();
    const imgurl = json.image;

    await interaction.reply({ content: imgurl, ephemeral: false });
  } else if (subCommand === "panda") {
    const response = await fetch("https://some-random-api.com/animal/panda");
    const json = await response.json();
    const imgurl = json.image;

    await interaction.reply({ content: imgurl, ephemeral: false });
  } else if (subCommand === "raccoon") {
    const response = await fetch("https://some-random-api.com/animal/raccoon");
    const json = await response.json();
    const imgurl = json.image;

    await interaction.reply({ content: imgurl, ephemeral: false });
  } else if (subCommand === "red-panda") {
    const response = await fetch(
      "https://some-random-api.com/animal/red_panda",
    );
    const json = await response.json();
    const imgurl = json.image;

    await interaction.reply({ content: imgurl, ephemeral: false });
  }
};

export default { data, execute };
