# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon

import discord
import aiohttp

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
        usage="api <subcommand> [args]",
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
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
        aliases=["mc"],
        description="Get someones minecraft character",
        usage="api minecraft <username>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    async def api_minecraft(self, context: Context, *, username: str) -> None:
        embed = discord.Embed(title=f"Minecraft character for {username}", color=0xBEBEFE)
        embed.set_image(url=f"https://mc-heads.net/body/{username}")

        await context.send(embed=embed)

    @api.command(
        name="mc-server",
        aliases=["mcserver", "mc-srv", "mcs"],
        description="Get info on a minecraft server",
        usage="api mc-server <username>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    async def api_mc_server(self, context: Context, *, host: str) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.mcsrvstat.us/3/{host}") as response:
                data = await response.json()

                if data["online"]:
                    embed = discord.Embed(
                        title=f"Server info for {host}", color=0xBEBEFE
                    )
                    embed.add_field(
                        name="Players", value=f"```{data['players']['online']}/{data['players']['max']}```", inline=False
                    )

                    if "software" in data:
                        embed.add_field(
                            name="Version", value=f"```{data['version']} ({data['software']})```", inline=False
                        )
                    else:
                        embed.add_field(
                            name="Version", value=f"```{data['version']}```", inline=False
                        )

                    embed.add_field(
                        name="MOTD", value=f"```{data['motd']['clean'][0]}```", inline=False
                    )

                    if "list" in data["players"]:
                        players = [p["name"] for p in data["players"]["list"]]
                        players = ", ".join(players)


                        embed.add_field(
                            name="Online players", value=f"```{players}```", inline=False
                        )

                    if "plugins" in data:
                        plugins = [p["name"] for p in data["plugins"]]
                        plugins = ", ".join(plugins)

                        embed.add_field(
                            name="Plugins", value=f"```{plugins}```", inline=False
                        )

                    if "mods" in data:
                        mods = [m["name"] for m in data["mods"]]
                        mods = ", ".join(mods)

                        embed.add_field(
                            name="Mods", value=f"```{mods}```", inline=False
                        )

                    await context.send(embed=embed)
                else:
                    await context.send("The server is offline")

async def setup(bot) -> None:
    await bot.add_cog(Api(bot))
