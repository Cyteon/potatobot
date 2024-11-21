import { SlashCommandSubcommandBuilder } from "discord.js";

const data = new SlashCommandSubcommandBuilder()
    .setName("play")
    .setDescription("Play a song")
    .addStringOption((option) =>
        option
            .setName("query")
            .setDescription("The song to play")
            .setRequired(true),
    );

const execute = async function (interaction) {
    await interaction.deferReply();

    let query = interaction.options.getString("query");

    if (!interaction.member.voice.channelId) {
      return interaction.editReply("You need to be in a voice channel!");
    }

    if (!query) {
      return interaction.editReply("You need to input a query")
    }

    const player = await interaction.client.kazagumo.createPlayer({
      guildId: interaction.guildId,
      voiceId: interaction.member.voice.channelId,
      textId: interaction.channelId,
      mute: false,
      volume: 100,
    });

    const result = await interaction.client.kazagumo.search(query, {
      requester: interaction.user,
    });

    if (!result.tracks.length) return interaction.editReply("No tracks found!");

    if (result.type === "PLAYLIST") {
      player.queue.add(result.tracks);
    } else {
      player.queue.add(result.tracks[0]);
    }

    await interaction.editReply({
      content:
        result.type === "PLAYLIST"
          ? `Queued ${result.tracks.length} from ${result.playlistName}`
          : `Queued ${result.tracks[0].title}`,
      embeds: [
        {
          title: result.tracks[0].title,
          thumbnail: {
            url: `https://img.youtube.com/vi/${result.tracks[0].identifier}/hqdefault.jpg`,
          },
          fields: [
            {
              name: "Duration",
              value: result.tracks[0].isStream
                ? `\`\`\`Live Stream\`\`\``
                : `\`\`\`${new Date(result.tracks[0].length).toISOString().substr(11, 8)}\`\`\``,
              inline: true
            },
            {
              name: "Author",
              value: `\`\`\`${result.tracks[0].author}\`\`\``,
              inline: true
            },
            {
              name: "Platform",
              value: `\`\`\`${result.tracks[0].sourceName}\`\`\``,
              inline: true
            },
          ],
          url: result.tracks[0].uri,
          color: 0x56b3fa,
        },
      ],
    });

    if (!player.playing && !player.paused) player.play();
    await interaction.guild.members.me.voice.setMute(false);
}

export default { data, execute };