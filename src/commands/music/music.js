import { SlashCommandBuilder } from "discord.js";
import { KazagumoTrack } from "kazagumo";

const data = new SlashCommandBuilder()
  .setName("music")
  .setDescription("Music commands")
  .addSubcommand((cmd) =>
    cmd
      .setName("play")
      .setDescription("Play a song")
      .addStringOption((option) =>
        option
          .setName("query")
          .setDescription("The song to play")
          .setRequired(true),
      ),
  )
  .addSubcommand((cmd) =>
    cmd
      .setName("volume")
      .setDescription("Change the volume")
      .addIntegerOption((option) =>
        option
          .setName("volume")
          .setDescription("The volume to set")
          .setRequired(true),
      ),
  );

const execute = async function (interaction) {
  const subcommand = interaction.options.getSubcommand();

  if (subcommand == "play") {
    let query = interaction.options.getString("query");

    if (!interaction.member.voice.channelId) {
      return interaction.reply(
        "You need to be in a voice channel to play music!",
      );
    }

    const player = await interaction.client.kazagumo.createPlayer({
      guildId: interaction.guildId,
      voiceId: interaction.member.voice.channelId,
      textId: interaction.channelId,
      volume: 100,
    });

    const result = await interaction.client.kazagumo.search(query, {
      requester: interaction.user.id,
    });

    if (!result.tracks.length) return interaction.reply("No results found!");

    if (result.type === "PLAYLIST") {
      player.queue.add(result.tracks);
    } else {
      player.queue.add(result.tracks[0]);
    }

    await interaction.reply({
      embeds: [
        {
          title: result.tracks[0].title,
          fields: [
            {
              name: "Duration",
              value: result.tracks[0].isStream
                ? "Live Stream"
                : new Date(result.tracks[0].length).toISOString().substr(11, 8),
            },
            {
              name: "Author",
              value: result.tracks[0].author,
            },
            {
              name: "Platform",
              value: result.tracks[0].sourceName,
            },
          ],
          url: result.tracks[0].uri,
          color: 0x56b3fa,
        },
      ],
    });

    if (!player.playing && !player.paused) player.play(); // TODO: FIX
  } else if (subcommand == "volume") {
    const volume = interaction.options.getInteger("volume");

    const player = interaction.client.shoukaku.getPlayer(interaction.guildId);

    if (!player) {
      return await interaction.reply("I'm not playing anything.");
    }

    await player.setVolume(volume);

    await interaction.reply(`Volume set to ${volume}.`);
  }
};

export default { data, execute };
