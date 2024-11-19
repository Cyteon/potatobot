import axios from "axios";
import { SlashCommandBuilder } from "discord.js";
import { KazagumoTrack } from "kazagumo";

/*
 Writer-Of-Comment : Ducky
 Info: Uhh so the code is AIO, it has all the commands. im so fucking confused. 
*/

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
  )
  .addSubcommand((cmd) =>
    cmd.setName("pause").setDescription("Pause the current song"),
  )
  .addSubcommand((cmd) =>
    cmd.setName("resume").setDescription("Resume the current song"),
  )
  .addSubcommand((cmd) =>
    cmd.setName("leave").setDescription("Leave the voice channel"),
  );

const execute = async function (interaction) {
  const subcommand = interaction.options.getSubcommand();

  if (subcommand == "play") {
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

        console.log(`https://img.youtube.com/vi/${result.tracks[0].identifier}/hqdefault.jpg`)
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
  } else if (subcommand == "volume") {
    const volume = interaction.options.getInteger("volume");

    const player = interaction.client.kazagumo.getPlayer(interaction.guildId);

    if (!player) {
      return await interaction.reply("I'm not playing anything.");
    }

    await player.setVolume(volume);

    await interaction.reply(`Volume set to ${volume}.`);
  } else if (subcommand == "pause") {
    const player = interaction.client.kazagumo.getPlayer(interaction.guildId);

    if (!player) {
      return await interaction.reply("I'm not playing anything.");
    }

    if (player.paused) {
      return await interaction.reply("Player is already paused.");
    }

    await player.pause(true);

    await interaction.reply("Player paused.");
  } else if (subcommand == "resume") {
    const player = interaction.client.kazagumo.getPlayer(interaction.guildId);

    if (!player) {
      return await interaction.reply("I'm not playing anything.");
    }

    if (!player.paused) {
      return await interaction.reply("Player is already playing.");
    }

    await player.pause(false);

    await interaction.reply("Player resumed.");
  } else if (subcommand == "leave") {
    const player = interaction.client.kazagumo.getPlayer(interaction.guildId);

    if (!player) {
      return await interaction.reply("I'm not playing anything.");
    }

    await player.destroy();

    await interaction.reply("Left the voice channel.");
  } else if (subcommand == "filter") {
    const filterSubcommand = interaction.options.getSubcommand();

    const player = interaction.client.kazagumo.getPlayer(interaction.guildId);

    if (!player) {
      return await interaction.reply("I'm not playing anything.");
    }

    if (filterSubcommand == "speed") {
      const speed = interaction.options.getNumber("speed");

      await player.setFilters({
        speed: speed,
      });

      await interaction.reply(`Speed set to ${speed}.`);
    }
  } else if (subcommand == "leave") {
    const player = interaction.client.kazagumo.getPlayer(interaction.guildId);

    if (!player) {
      return await interaction.reply("I'm not playing anything.");
    }

    await player.destroy();

    await interaction.reply("Left the voice channel.");
  }
};

export default { data, execute };
