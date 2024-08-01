# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon

import re
import os
import logging

import discord
import lavalink
from discord.ext import commands
from discord.ext.commands import Context
from lavalink.events import TrackStartEvent, QueueEndEvent
from lavalink.errors import ClientError
from lavalink.filters import LowPass, Timescale
from lavalink.server import LoadType

url_rx = re.compile(r'https?://(?:www\.)?.+')

from utils import Checks

logger = logging.getLogger("discord_bot")


host = os.getenv("LAVALINK_HOST")
port = os.getenv("LAVALINK_PORT")
password = os.getenv("LAVALINK_PASSWORD")
region = os.getenv("LAVALINK_REGION")
name = os.getenv("LAVALINK_NAME")

class LavalinkVoiceClient(discord.VoiceProtocol):
    def __init__(self, client: discord.Client, channel: discord.abc.Connectable):
        self.client = client
        self.channel = channel
        self.guild_id = channel.guild.id
        self._destroyed = False

        if not hasattr(self.client, 'lavalink'):
            self.client.lavalink = lavalink.Client(client.user.id)
            self.client.lavalink.add_node(host=host, port=port, password=password,
                                          region=region, name=name)

        self.lavalink = self.client.lavalink

    async def on_voice_server_update(self, data):
        lavalink_data = {
            't': 'VOICE_SERVER_UPDATE',
            'd': data
        }
        await self.lavalink.voice_update_handler(lavalink_data)

    async def on_voice_state_update(self, data):
        channel_id = data['channel_id']

        if not channel_id:
            await self._destroy()
            return

        self.channel = self.client.get_channel(int(channel_id))

        lavalink_data = {
            't': 'VOICE_STATE_UPDATE',
            'd': data
        }

        await self.lavalink.voice_update_handler(lavalink_data)

    async def connect(self, *, timeout: float, reconnect: bool, self_deaf: bool = False, self_mute: bool = False) -> None:
        self.lavalink.player_manager.create(guild_id=self.channel.guild.id)
        await self.channel.guild.change_voice_state(channel=self.channel, self_mute=self_mute, self_deaf=self_deaf)

    async def disconnect(self, *, force: bool = False) -> None:
        player = self.lavalink.player_manager.get(self.channel.guild.id)

        if not force and not player.is_connected:
            return

        await self.channel.guild.change_voice_state(channel=None)
        player.channel_id = None
        await self._destroy()

    async def _destroy(self):
        self.cleanup()

        if self._destroyed:
            return

        self._destroyed = True

        try:
            await self.lavalink.player_manager.destroy(self.guild_id)
        except ClientError:
            pass


class Music(commands.Cog, name="🎵 Music"):
    def __init__(self, bot):
        self.bot = bot

        if not hasattr(bot, 'lavalink'):
            bot.lavalink = lavalink.Client(bot.user.id)
            bot.lavalink.add_node(host=host, port=port, password=password,
                                  region=region, name=name)

        self.lavalink: lavalink.Client = bot.lavalink
        self.lavalink.add_event_hooks(self)

    def cog_unload(self):
        self.lavalink._event_hooks.clear()

    async def cog_command_error(self, context, error):
        if isinstance(error, commands.CommandInvokeError):
            await context.send(error.original)

    async def create_player(context: commands.Context):
        if context.guild is None:
            raise commands.NoPrivateMessage()

        player = context.bot.lavalink.player_manager.create(context.guild.id)

        should_connect = context.command.name in ('play',)

        voice_client = context.voice_client

        if not context.author.voice or not context.author.voice.channel:
            if voice_client is not None:
                raise commands.CommandInvokeError('You need to join my voice channel first.')

            raise commands.CommandInvokeError('Join a voicechannel first.')

        voice_channel = context.author.voice.channel

        if voice_client is None:
            if not should_connect:
                raise commands.CommandInvokeError("I'm not playing music.")

            permissions = voice_channel.permissions_for(context.me)

            if not permissions.connect or not permissions.speak:
                raise commands.CommandInvokeError('I need the `CONNECT` and `SPEAK` permissions.')

            if voice_channel.user_limit > 0:
                if len(voice_channel.members) >= voice_channel.user_limit and not context.me.guild_permissions.move_members:
                    raise commands.CommandInvokeError('Your voice channel is full!')

            player.store('channel', context.channel.id)
            await context.author.voice.channel.connect(cls=LavalinkVoiceClient)
        elif voice_client.channel.id != voice_channel.id:
            raise commands.CommandInvokeError('You need to be in my voicechannel.')

        return True

    @lavalink.listener(TrackStartEvent)
    async def on_track_start(self, event: TrackStartEvent):
        guild_id = event.player.guild_id
        channel_id = event.player.fetch('channel')
        guild = self.bot.get_guild(guild_id)

        if not guild:
            return await self.lavalink.player_manager.destroy(guild_id)

        channel = guild.get_channel(channel_id)

        if channel:
            await channel.send(f'Now playing: {event.track.title} by {event.track.author}')
            logger.info(f"Now playing {event.track.title} in {guild} ({guild.id})")



    @lavalink.listener(QueueEndEvent)
    async def on_queue_end(self, event: QueueEndEvent):
        guild_id = event.player.guild_id
        guild = self.bot.get_guild(guild_id)

        if guild is not None:
            await guild.voice_client.disconnect(force=True)

    @commands.hybrid_command(
        name="play",
        description="Searches and plays a song from a given query.",
        aliases=['p'],
        usage="play <query or link>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(create_player)
    async def play(self, context, *, query: str):
        player = self.bot.lavalink.player_manager.get(context.guild.id)
        query = query.strip('<>')

        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        results = await player.node.get_tracks(query)

        embed = discord.Embed(color=discord.Color.blurple())

        if results.load_type == LoadType.EMPTY:
            return await context.send("I couldn't find any tracks for that query.")
        elif results.load_type == LoadType.PLAYLIST:
            tracks = results.tracks

            for track in tracks:
                player.add(track=track, requester=context.author.id)

            embed.title = 'Playlist Enqueued!'
            embed.description = f'{results.playlist_info.name} - {len(tracks)} tracks'
        else:
            track = results.tracks[0]
            embed.title = 'Track Enqueued'
            embed.description = f'[{track.title}]({track.uri})'

            player.add(track=track, requester=context.author.id)

        await context.send(embed=embed)

        if not player.is_playing:
            await player.play()

    @commands.hybrid_command(
        name="skip",
        description="Skip to the next song in the queue",
        usage="skip"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(create_player)
    async def skip(self, context):
        await self.bot.lavalink.player_manager.get(context.guild.id).skip()

    @commands.hybrid_command(
        name="pause",
        description="Pauses the currently playing track",
        usage="pause"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(create_player)
    async def pause(self, context):
        player = self.bot.lavalink.player_manager.get(context.guild.id)

        if player.is_playing:
            await player.set_pause(True)
            await context.send('⏸ | Paused the player.')

    @commands.hybrid_command(
        name="resume",
        description="Resumes the currently paused track",
        usage="resume"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(create_player)
    async def resume(self, context):
        player = self.bot.lavalink.player_manager.get(context.guild.id)

        if player.paused:
            await player.set_pause(False)
            await context.send('▶ | Resumed the player.')

    @commands.hybrid_command(
        name="loop",
        description="Enables/disables the loop on the current track",
        aliases=['repeat'],
        usage="loop"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(create_player)
    async def loop(self, context):
        player = self.bot.lavalink.player_manager.get(context.guild.id)
        player.loop = not player.loop

        await context.send(f"🔁 | {'Enabled' if player.loop else 'Disabled'} loop.")

    @commands.hybrid_group(
        name="filter",
        description="Commands for managing filters.",
        usage="filter <filter> <args>"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def filter(self, context: Context) -> None:
        prefix = await self.bot.get_prefix(context)

        cmds = "\n".join([f"{prefix}filter {cmd.name} - {cmd.description}" for cmd in self.filter.walk_commands()])

        embed = discord.Embed(
            title=f"Help: Filter", description="List of available commands:", color=0xBEBEFE
        )
        embed.add_field(
            name="Commands", value=f"```{cmds}```", inline=False
        )

        await context.send(embed=embed)

    @filter.command(
        name="lowpass",
        description="Sets the strength of the low pass filter",
        usage="filer lowpass <strength>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(create_player)
    async def lowpass(self, context, strength: float = 0.0):
        player = self.bot.lavalink.player_manager.get(context.guild.id)

        strength = max(0, strength)
        strength = min(100, strength)

        if strength < 1 and strength != 0.0:
            return await context.send('The strength must be greater than 1.')

        embed = discord.Embed(color=discord.Color.blurple(), title='Low Pass Filter')

        if strength == 0.0:
            await player.remove_filter('lowpass')
            embed.description = 'Disabled **Low Pass Filter**'
            return await context.send(embed=embed)

        low_pass = LowPass()
        low_pass.update(smoothing=strength)

        await player.set_filter(low_pass)

        embed.description = f'Set **Low Pass Filter** strength to {strength}.'
        await context.send(embed=embed)


    @filter.command(
        name="pitch",
        description="Sets the player pitch",
        aliases=['ptch'],
        usage="filter pitch <pitch>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(create_player)
    async def pitch(self, context: Context, pitch: float):
        player = self.bot.lavalink.player_manager.get(context.guild.id)

        pitch = max(0.1, pitch)

        timescale = Timescale()
        timescale.pitch = pitch
        await player.set_filter(timescale)

        await context.send(f"🎵 | Set the player pitch to {pitch}.")


    @filter.command(
        name="speed",
        description="Sets the player speed",
        aliases=['spd'],
        usage="filter speed <speed>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(create_player)
    async def speed(self, context: Context, speed: float):
        player = self.bot.lavalink.player_manager.get(context.guild.id)

        speed = max(0.1, speed)

        timescale = Timescale()
        timescale.speed = speed
        await player.set_filter(timescale)

        await context.send(f"🏃 | Set the player speed to {speed}.")

    @commands.hybrid_command(
        name="disconnect",
        description="Disconnects the player from the voice channel and clears the queue",
        aliases=['dc'],
        usage="disconnect"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(create_player)
    async def disconnect(self, context):
        player = self.bot.lavalink.player_manager.get(context.guild.id)

        player.queue.clear()
        await player.stop()
        await context.voice_client.disconnect(force=True)
        await context.send('✳ | Disconnected.')

    @commands.hybrid_command(
        name="volume",
        description="Sets the player volume",
        aliases=['vol'],
        usage="volume <volume>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(create_player)
    async def volume(self, context: Context, volume: int):
        player = self.bot.lavalink.player_manager.get(context.guild.id)

        volume = max(1, volume)
        volume = min(100, volume)

        await player.set_volume(volume)
        await context.send(f"🔊 | Set the player volume to {volume}.")


async def setup(bot) -> None:
    await bot.add_cog(Music(bot))
