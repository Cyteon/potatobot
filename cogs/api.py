# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon

import discord
import random

from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

from utils import Checks

class Api(commands.Cog, name="🌐 API"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_group(
        name="api",
        description="Commands for diffrent APIs",
        usage="api <subcommand> <subcommand>",
    )
    @commands.check(Checks.is_not_blacklisted)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def api(self, context: Context) -> None:
        prefix = await self.bot.get_prefix(context)

        cmds = "\n".join([f"{prefix}api {cmd.name} - {cmd.description}" for cmd in self.api.walk_commands()])

        embed = discord.Embed(
            title=f"Help: Api", description="List of available commands:", color=0xBEBEFE
        )
        embed.add_field(
            name="Commands", value=f"```{cmds}```", inline=False
        )

        await context.send(embed=embed)

    @api.command(
        name="minecraft",
        description="Get someones minecraft character",
        usage="api minecraft <username>"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def api_minecraft(self, context: Context, *, username: str) -> None:
        embed = discord.Embed(title=f"Minecraft character for {username}", color=0xBEBEFE)
        embed.set_image(url=f"https://mc-heads.net/body/{username}")

        await context.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Api(bot))
