"""
The MIT License (MIT)

Copyright (c) 2022 Ogiroid Development Team

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
"""


import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

from utils import Checks


class Github(commands.Cog, name="🖧 Github"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_group(
        name="github",
        description="Commands related to GitHub",
        usage="github <subcommand> [args]",
        aliases=["gh"],
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def github(self, context: Context) -> None:
        prefix = await self.bot.get_prefix(context)

        cmds = "\n".join([f"{prefix}github {cmd.name} - {cmd.description}" for cmd in self.github.walk_commands()])

        embed = discord.Embed(
            title=f"Help: Github", description="List of available commands:", color=0xBEBEFE
        )
        embed.add_field(
            name="Commands", value=f"```{cmds}```", inline=False
        )

        await context.send(embed=embed)

    # Command to get information about a GitHub user
    @github.command(
        name="user",
        description="Gets the Profile of the github person.",
        usage="github user <username>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    async def ghuser(self, context, user: str):
        async with aiohttp.ClientSession() as session:
            person_raw = await session.get(
                f"https://api.github.com/users/{user}"
            )
            if person_raw.status != 200:
                return await context.send("User not found!")
            else:
                person = await person_raw.json()
            # Returning an Embed containing all the information:
            embed = discord.Embed(
                title=f"GitHub Profile: {person['login']}",
                description=f"**Bio:** {person['bio']}",
                color=0xFFFFFF,
            )
            embed.set_thumbnail(url=f"{person['avatar_url']}")
            embed.add_field(
                name="Username 📛: ", value=f"{person['name']}", inline=True
            )
            # embed.add_field(name="Email ✉: ", value=f"{person['email']}", inline=True) Commented due to GitHub not responding with the correct email
            embed.add_field(
                name="Repos 📁: ", value=f"{person['public_repos']}", inline=True
            )
            embed.add_field(
                name="Location 📍: ", value=f"{person['location']}", inline=True
            )
            embed.add_field(
                name="Company 🏢: ", value=f"{person['company']}", inline=True
            )
            embed.add_field(
                name="Followers 👥: ", value=f"{person['followers']}", inline=True
            )
            embed.add_field(
                name="Website 🖥️: ", value=f"{person['blog']}", inline=True
            )

            await context.send(embed=embed, view=ProfileButton(url=person["html_url"]))

    # Command to get search for GitHub repositories:
    @github.command(
        name="repo",
        description="Searches for the specified repo.",
        usage="github repo <repo>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    async def ghsearchrepo(self, context, query: str):
        pages = 1
        url = f"https://api.github.com/search/repositories?q={query}&{pages}"
        async with aiohttp.ClientSession() as session:
            repos_raw = await session.get(url)
            if repos_raw.status != 200:
                return await context.send("Repo not found!")
            else:
                repos = (
                    await repos_raw.json()
                )  # Getting first repository from the query
            repo = repos["items"][0]
            # Returning an Embed containing all the information:
            embed = discord.Embed(
                title=f"GitHub Repository: {repo['name']}",
                description=f"**Description:** {repo['description']}",
                color=0xFFFFFF,
            )
            embed.set_thumbnail(url=f"{repo['owner']['avatar_url']}")
            embed.add_field(
                name="Author 🖊:",
                value=f"__[{repo['owner']['login']}]({repo['owner']['html_url']})__",
                inline=True,
            )
            embed.add_field(
                name="Stars ⭐:", value=f"{repo['stargazers_count']}", inline=True
            )
            embed.add_field(
                name="Forks 🍴:", value=f"{repo['forks_count']}", inline=True
            )
            embed.add_field(
                name="Language 💻:", value=f"{repo['language']}", inline=True
            )
            embed.add_field(
                name="Size 🗃️:",
                value=f"{round(repo['size'] / 1000, 2)} MB",
                inline=True,
            )
            if repo["license"]:
                spdx_id = repo["license"]["spdx_id"]
                embed.add_field(
                    name="License name 📃:",
                    value=f"{spdx_id if spdx_id != 'NOASSERTION' else repo['license']['name']}",
                    inline=True,
                )
            else:
                embed.add_field(
                    name="License name 📃:",
                    value="This Repo doesn't have a license",
                    inline=True,
                )

            await context.send(embed=embed, view=RepoButton(url=repo["html_url"]))

class ProfileButton(discord.ui.View):
    def __init__(self, url: str):
        super().__init__()

        self.add_item(discord.ui.Button(label="GitHub Profile", style=discord.ButtonStyle.url, url=url))

class RepoButton(discord.ui.View):
    def __init__(self, url: str):
        super().__init__()

        self.add_item(discord.ui.Button(label="GitHub Repository", style=discord.ButtonStyle.url, url=url))

async def setup(bot) -> None:
    await bot.add_cog(Github(bot))
