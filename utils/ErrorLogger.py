# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon

import os
import sys
import json

import discord
from discord import Webhook
import aiohttp
import traceback

if not os.path.isfile(f"./config.json"):
    sys.exit("'config.json' not found! Please add it and try again.")
else:
    with open(f"./config.json") as file:
        config = json.load(file)

async def command_error(error, context):
    async with aiohttp.ClientSession() as session:
        command_error_webhook = Webhook.from_url(config["command_error_webhooks"], session=session)

        embed = discord.Embed(
            title="An error occurred!",
            description=f"```{error}```",
            color=discord.Color.red()
        )

        embed.add_field(
            name="Author",
            value=f"{context.author.mention}",
            inline=False
        )

        embed.add_field(
            name="Guild",
            value=f"`{context.guild.name}` (`{context.guild.id}`)",
            inline=False
        )

        if context.command:
            embed.add_field(
                name="Command",
                value=f"`{context.command.name}`",
                inline=False
            )

        await command_error_webhook.send(embed=embed, username = "PotatoBot - Error Logger")
async def error(self, event_method, *args, **kwargs):
    async with aiohttp.ClientSession() as session:
        error_webhook = Webhook.from_url(config["error_webhooks"], session=session)

        embed = discord.Embed(
            title="An error occurred!",
            description=f"```{traceback.format_exc()}```",
            color=discord.Color.red()
        )

        embed.add_field(
            name="Event Method",
            value=f"`{event_method}`",
            inline=False
        )

        await error_webhook.send(embed=embed, username="PotatoBot - Error Logger")
