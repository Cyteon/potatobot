import { SlashCommandBuilder } from "@discordjs/builders";

const data = new SlashCommandBuilder()
    .setName('random')
    .setDescription('Gets a random image of something.')
    .addSubcommand(subcommand =>
        subcommand
            .setName('bird')
            .setDescription('Get a random bird image'))
    .addSubcommand(subcommand =>
        subcommand
            .setName('boykisser')
            .setDescription('Get a random boykisser image'))
    .addSubcommand(subcommand =>
        subcommand
            .setName('cat')
            .setDescription('Get a random cat image'))
    .addSubcommand(subcommand =>
        subcommand
            .setName('coffee')
            .setDescription('Get a random coffee image'))
    .addSubcommand(subcommand =>
        subcommand
            .setName('dog')
            .setDescription('Get a random dog image'))
    .addSubcommand(subcommand =>
        subcommand
            .setName('fox')
            .setDescription('Get a random fox image'))
    .addSubcommand(subcommand =>
        subcommand
            .setName('gary')
            .setDescription('Get a random gary image'))
    .addSubcommand(subcommand =>
        subcommand
            .setName('gary-joke')
            .setDescription('Get a random gary joke'))
    .addSubcommand(subcommand =>
        subcommand
            .setName('gary-quote')
            .setDescription('Get a random gary quote'))
    .addSubcommand(subcommand =>
        subcommand
            .setName('gayrate')
            .setDescription('Get your gay rate'))
    .addSubcommand(subcommand =>
        subcommand
            .setName('kangaroo')
            .setDescription('Get a random kangaroo image'))
    .addSubcommand(subcommand =>
        subcommand
            .setName('koala')
            .setDescription('Get a random koala image'))
    .addSubcommand(subcommand =>
        subcommand
            .setName('panda')
            .setDescription('Get a random panda image'))
    .addSubcommand(subcommand =>
        subcommand
            .setName('raccoon')
            .setDescription('Get a random raccoon image'))
    .addSubcommand(subcommand =>
        subcommand
            .setName('red-panda')
            .setDescription('Get a random red panda image'))

const execute = async function (interaction) {
    const { options } = interaction;
    const subCommand = options.getSubcommand();
    const garyHeaders = {
        'Content-Type': 'application/json',
        'api_key': process.env.GARY_API_KEY,
    };

    if (subCommand === "bird") {
        response = await fetch("https://some-random-api.com/animal/bird");
        json = await response.json();
        imgurl = json.image;
    
        await interaction.reply({ content: imgurl, ephemeral: false });
    } else if (subCommand === "boykisser") {
        response = await fetch("https://api.gizzy.is-a.dev/api/random?redirect=0");
        json = await response.json();
        imgurl = json.image;
    
        await interaction.reply({ content: imgurl, ephemeral: false });
    } else if (subCommand === "cat") {
        response = await fetch("https://some-random-api.com/animal/cat");
        json = await response.json();
        imgurl = json.image;

        await interaction.reply({ content: imgurl, ephemeral: false });
    } else if (subCommand === "coffee") {
        response = await fetch("https://coffee.alexflipnote.dev/random.json");
        json = await response.json();
        imgurl = json.file;

        await interaction.reply({ content: imgurl, ephemeral: false });
    } else if (subCommand === "dog") {
        response = await fetch('https://some-random-api.com/animal/dog');
        json = await response.json();
        imgurl = json.image;

        await interaction.reply({ content: imgurl, ephemeral: false });
    } else if (subCommand === "fox") {
        response = await fetch('https://some-random-api.com/animal/fox');
        json = await response.json();
        imgurl = json.image;

        await interaction.reply({ content: imgurl, ephemeral: false });
    } else if (subCommand === "gary") {
        response = await fetch('https://garybot.dev/api/gary', { method: 'GET', garyHeaders });
        json = await response.json();
        imgurl = json.image;

        await interaction.reply({ content: imgurl, ephemeral: false });
    } else if (subCommand === "gary-joke") {
        response = await fetch('https://garybot.dev/api/joke', { method: 'GET', garyHeaders });
        json = await response.json();
        joke = json.joke;

        await interaction.reply({ content: joke, ephemeral: false });
    } else if (subCommand === "gary-quote") {
        response = await fetch('https://garybot.dev/api/quote', { method: 'GET', garyHeaders });
        json = await response.json();
        quote = json.quote;

        await interaction.reply({ content: quote, ephemeral: false });
    } else if (subCommand === "gayrate") {
        const emojis = ["😳", "😳", "😳", "😳", "😳", "😳", "😳", "😳", "😳", "😳", "🏳️‍🌈", "🔥"]
        const percentage = Math.floor(Math.random() * 100) + 1;
        let emoji;

        if (percentage > 90) {
            emoji = "🌈"
        } else if (percentage < 10) {
            emoji = "🔥"
        } else {
            emoji = emojis[Math.floor(emojis.length * Math.random())];
        }

        await interaction.reply(`<@${user}> is ${percentage}% gay ${emoji}`)
    } else if (subCommand === "kangaroo") {
        response = await fetch('https://some-random-api.com/animal/kangaroo');
        json = await response.json();
        imgurl = json.image;

        await interaction.reply({ content: imgurl, ephemeral: false });
    } else if (subCommand === "koala") {
        response = await fetch('https://some-random-api.com/animal/koala');
        json = await response.json();
        imgurl = json.image;

        await interaction.reply({ content: imgurl, ephemeral: false });
    } else if (subCommand === "panda") {
        response = await fetch('https://some-random-api.com/animal/panda');
        json = await response.json();
        imgurl = json.image;

        await interaction.reply({ content: imgurl, ephemeral: false });
    } else if (subCommand === "raccoon") {
        response = await fetch('https://some-random-api.com/animal/raccoon');
        json = await response.json();
        imgurl = json.image;

        await interaction.reply({ content: imgurl, ephemeral: false });
    } else if (subCommand === "red-panda") {
        response = await fetch('https://some-random-api.com/animal/red_panda');
        json = await response.json();
        imgurl = json.image;

        await interaction.reply({ content: imgurl, ephemeral: false });
    }
};

export default { data, execute };