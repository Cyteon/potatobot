# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon

import discord
from discord.ext import commands
from discord.ext.commands import Context
from utils import CONSTANTS, DBClient, Checks, CachedDB

from ui.starboard import JumpToMessageView

client = DBClient.client
db = client.potatobot

class Starboard(commands.Cog, name="⭐ Starboard"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload) -> None:
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        if message.author.bot:
            return

        col = db["guilds"]
        guild = await CachedDB.find_one(col, {"id": payload.guild_id})

        if not guild:
            return

        if "starboard" not in guild:
            return

        if guild["starboard"]["channel"] == 0:
            return

        if "enabled" in guild["starboard"]:
            if not guild["starboard"]["enabled"]:
                return

        starboard_col = db["starboard"]
        starboard_message = await CachedDB.find_one(starboard_col, {"message_id": message.id})
        starboard_channel = self.bot.get_channel(guild["starboard"]["channel"])

        star_reactions = 0
        for r in message.reactions:
            if r.emoji == "⭐":
                star_reactions = r.count

        if payload.emoji.name == "⭐":
            if star_reactions >= guild["starboard"]["threshold"]:
                if not starboard_message:
                    embed = discord.Embed(
                        description=message.content,
                        color=0xFFD700,
                        timestamp=message.created_at
                    )

                    embed.set_author(name=message.author, icon_url=message.author.display_avatar.url)

                    if message.attachments:
                        embed.set_image(url=message.attachments[0].url)

                    label = "⭐ " + str(star_reactions)

                    msg = await starboard_channel.send(label, embed=embed, view=JumpToMessageView(message))

                    newdata = {
                        "message_id": message.id,
                        "starboard_id": msg.id
                    }

                    starboard_col.insert_one(newdata)
                else:
                    embed = discord.Embed(
                        description=message.content,
                        color=0xFFD700,
                        timestamp=message.created_at
                    )

                    embed.set_author(name=message.author, icon_url=message.author.display_avatar.url)

                    if message.attachments:
                        embed.set_image(url=message.attachments[0].url)

                    label = "⭐ " + str(star_reactions)

                    starboard_message = await starboard_channel.fetch_message(starboard_message["starboard_id"])

                    await starboard_message.edit(content=label, embed=embed, view=JumpToMessageView(message))

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload) -> None:
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        if message.author.bot:
            return

        col = db["guilds"]
        guild = await CachedDB.find_one(col, {"id": payload.guild_id})

        if not guild:
            return

        if "starboard" not in guild:
            return

        if guild["starboard"]["channel"] == 0:
            return

        if "enabled" in guild["starboard"]:
            if not guild["starboard"]["enabled"]:
                return

        star_reactions = 0
        for r in message.reactions:
            if r.emoji == "⭐":
                star_reactions = r.count

        starboard_col = db["starboard"]
        starboard_message = await CachedDB.find_one(starboard_col, {"message_id": message.id})
        starboard_channel = self.bot.get_channel(guild["starboard"]["channel"])

        if not starboard_channel:
            return

        if payload.emoji.name == "⭐":
            embed = discord.Embed(
                description=message.content,
                color=0xFFD700,
                timestamp=message.created_at
            )

            embed.set_author(name=message.author, icon_url=message.author.display_avatar.url)

            label = "⭐ " + str(star_reactions)

            if message.attachments:
                embed.set_image(url=message.attachments[0].url)

            starboard_message = await starboard_channel.fetch_message(starboard_message["starboard_id"])

            await starboard_message.edit(content=label, embed=embed, view=JumpToMessageView(message))

    @commands.hybrid_group(
        name="starboard",
        description="Commands for managing the starboard.",
        usage="starboard <subcommand>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    async def starboard(self, context: Context) -> None:
        subcommands = [cmd for cmd in self.starboard.walk_commands()]

        data = []

        for subcommand in subcommands:
            print(subcommand)
            description = subcommand.description.partition("\n")[0]
            data.append(f"{await self.bot.get_prefix(context)}starboard {subcommand.name} - {description}")

        help_text = "\n".join(data)
        embed = discord.Embed(
            title=f"Help: Starboard", description="List of available commands:", color=0xBEBEFE
        )
        embed.add_field(
            name="Commands", value=f"```{help_text}```", inline=False
        )

        await context.send(embed=embed)

    @starboard.command(
        name="channel",
        description="Set the starboard channel.",
        usage="starboard channel <channel>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @commands.has_permissions(manage_channels=True)
    async def set_starboard(self, context: Context, channel: discord.TextChannel) -> None:
        col = db["guilds"]
        guild = await CachedDB.find_one(col, {"id": context.guild.id})

        if not guild:
            guild = CONSTANTS.guild_data_template(context.guild.id)
            await col.insert_one(CONSTANTS.guild_data_template(context.guild.id))

        newdata = {
            "$set": {
                "starboard.channel": channel.id
            }
        }

        await CachedDB.update_one(col, {"id": context.guild.id}, newdata)
        await context.send(f"Starboard channel set to {channel.mention}.")

    @starboard.command(
        name="threshold",
        description="Set the starboard threshold required to show in starboard channel",
        usage="starboard threshold <threshold>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @commands.has_permissions(manage_channels=True)
    async def set_threshold(self, context: Context, threshold: int) -> None:
        col = db["guilds"]
        guild = await CachedDB.find_one(col, {"id": context.guild.id})

        if not guild:
            guild = CONSTANTS.guild_data_template(context.guild.id)
            await col.insert_one(guild)

        newdata = {
            "$set": {
                "starboard.threshold": threshold
            }
        }

        await CachedDB.update_one(col, {"id": context.guild.id}, newdata)
        await context.send(f"Starboard threshold set to {threshold}.")

    @starboard.command(
        name="disable",
        description="Disable the starboard.",
        usage="starboard disable"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @commands.has_permissions(manage_channels=True)
    async def disable_starboard(self, context: Context) -> None:
        col = db["guilds"]
        guild = await CachedDB.find_one(col, {"id": context.guild.id})

        if not guild:
            guild = CONSTANTS.guild_data_template(context.guild.id)
            await col.insert_one(guild)

        newdata = {
            "$set": {
                "starboard.enabled": False
            }
        }

        await CachedDB.update_one(col, {"id": context.guild.id}, newdata)
        await context.send("Starboard disabled.")

    @starboard.command(
        name="enable",
        description="Enable the starboard.",
        usage="starboard enable"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)

    @commands.has_permissions(manage_channels=True)
    async def enable_starboard(self, context: Context) -> None:
        col = db["guilds"]
        guild = await CachedDB.find_one(col, {"id": context.guild.id})

        if not guild:
            guild = CONSTANTS.guild_data_template(context.guild.id)
            await col.insert_one(guild)

        newdata = {
            "$set": {
                "starboard.enabled": True
            }
        }

        await CachedDB.update_one(col, {"id": context.guild.id}, newdata)
        await context.send("Starboard enabled.")

async def setup(bot) -> None:
    await bot.add_cog(Starboard(bot))
