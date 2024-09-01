# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon

import discord
import random

from discord.ext import commands
from discord.ext.commands import Context

from utils import Checks

class Giveaway(commands.Cog, name="🎁 Giveaway"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_group(
        name="giveaway",
        description="Command to start or end giveaways",
        usage="giveaway"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @commands.has_permissions(manage_messages=True)
    async def giveaway(self, context: Context) -> None:
        prefix = await self.bot.get_prefix(context)

        cmds = "\n".join([f"{prefix}giveaway {cmd.name} - {cmd.description}" for cmd in self.giveaway.walk_commands()])

        embed = discord.Embed(
            title=f"Help: Giveaway", description="List of available commands:", color=0xBEBEFE
        )
        embed.add_field(
            name="Commands", value=f"```{cmds}```", inline=False
        )

        await context.send(embed=embed)

    @giveaway.command(
        name="start",
        description="Start a giveaway!",
        usage="giveaway start <reward>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @commands.has_permissions(manage_messages=True)
    async def giveaway_start(self, context: Context, *, reward: str) -> None:
        embed = discord.Embed(title="Giveaway!", description=reward, color=0xBEBEFE)

        message = await context.send(embed=embed)

        await message.add_reaction("🎁")

    @giveaway.command(
        name = "end",
        description = "Ends a poll using message id",
        usage = "giveaway end <message_id>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @commands.has_permissions(manage_messages=True)
    async def giveaway_end(self, context: Context, message_id) -> None:
        message_id = int(message_id)

        message = await context.fetch_message(message_id)

        users = []

        async for u in message.reactions[0].users():
            users.append(u)

        users.pop(users.index(self.bot.user))
        winner = random.choice(users)

        embed = discord.Embed(title="Giveaway ended!", description="The winner is: {0} 🎉🎉🎉".format(winner.mention), color=0xBEBEFE)

        await message.reply(winner.mention, embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Giveaway(bot))
