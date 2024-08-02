# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon

import discord
import os
import aiohttp

from cryptography.fernet import Fernet

from discord.ext import commands
from discord.ext.commands import Context

from utils import Checks, DBClient, CachedDB, CONSTANTS

db = DBClient.db

class Server(commands.Cog, name="⚙️ Server"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.prefixDB = bot.prefixDB

    @commands.command(
        name="prefix",
        description="Change the bot prefix",
        usage="prefix <symbol>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_channels=True)
    async def prefix(self, context: commands.Context, prefix: str = "none"):
        if prefix == "none":
            return await context.send("Current prefix is: `" + self.prefixDB.get(str(context.guild.id)) + "`")

        if prefix == "/":
            return await context.send("Prefix cannot be `/`")

        guild_id = str(context.guild.id)
        self.prefixDB.set(guild_id, prefix)
        self.prefixDB.dump()
        await context.send(f"Prefix set to {prefix}")

    @commands.hybrid_command(
        name="groq-api-key",
        description="Set API key for AI (run in private channel please)",
        usage="groq-api-key <key>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_channels=True)
    async def groq_api_key(self, context: commands.Context, key: str):
        c = db["guilds"]
        data = c.find_one({"id": context.guild.id})

        if not data:
            data = CONSTANTS.guild_data_template(context.guild.id)
            c.insert_one(data)

        cipher_suite = Fernet(os.getenv("HASHING_SECRET"))
        cipher_text = cipher_suite.encrypt(key.encode())

        try:
            await context.message.delete()
        except:
            pass

        if key == "NONE":
            cipher_text = "NONE"

        newdata = { "$set": { "groq_api_key": cipher_text } }

        c.update_one({"id": context.guild.id}, newdata)

        await context.send(f"Set groq api key")

    @commands.hybrid_command(
        name="stealemoji",
        description="Steal an emoji from another server.",
        usage="stealemoji <emoji> <name>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_emojis=True)
    @commands.bot_has_permissions(manage_emojis=True)
    async def stealemoji(self, context: Context, emoji: discord.PartialEmoji, name: str) -> None:
        try:
            emoji_bytes = await emoji.read()
            await context.guild.create_custom_emoji(
                name=name if name else emoji.name,
                image=emoji_bytes,
                reason=f"Emoji yoinked by {context.author} VIA {context.guild.me.name}",
            )
            await context.send(
                embed=discord.Embed(
                    description=f"Emoji Stolen",
                    color=discord.Color.random(),
                ).set_image(url=emoji.url)
            )
        except Exception as e:
            await context.send(str(e))

    @commands.hybrid_command(
        name="emojifromurl",
        description="Add an emoji from a URL.",
        usage="emojifromurl <url> <name>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_emojis=True)
    @commands.bot_has_permissions(manage_emojis=True)
    async def emojifromurl(self, context: Context, url: str, name: str) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    emoji_bytes = await response.read()
                    await context.guild.create_custom_emoji(
                        name=name,
                        image=emoji_bytes,
                        reason=f"Emoji added by {context.author} VIA {context.guild.me.name}",
                    )
                    await context.send(
                        embed=discord.Embed(
                            description=f"Emoji added",
                            color=discord.Color.random(),
                        ).set_image(url=url)
                    )
                else:
                    await context.send("Failed to download the emoji")

async def setup(bot) -> None:
    await bot.add_cog(Server(bot))
