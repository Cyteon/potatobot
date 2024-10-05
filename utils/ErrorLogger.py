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

def apply_context_errors(embed, context, ignore_message=False):
    embed.add_field(
        name="Author",
        value=f"{context.author.mention}",
        inline=True
    )

    if context.guild:
        embed.add_field(
            name="Guild",
            value=f"`{context.guild.name}` (`{context.guild.id}`)",
            inline=True
        )

    if context.command:
        embed.add_field(
            name="Command",
            value=f"`{context.command.name}`",
            inline=True
        )

    if context.message.content != "" and not ignore_message:
        embed.add_field(
            name="Message",
            value=f"```{context.message.content}```",
            inline=True
        )

    if context.interaction:
        options = context.interaction.data["options"]
        options = json.dumps(options, indent=2)

        embed.add_field(
            name="Interaction Options",
            value=f"```{options}```",
            inline=True
        )

async def command_error(error, context):
    async with aiohttp.ClientSession() as session:
        command_error_webhook = Webhook.from_url(config["command_error_webhook"], session=session)

        embed = discord.Embed(
            title="An error occurred!",
            description=f"```{error}```",
            color=discord.Color.red()
        )

        apply_context_errors(embed, context)

        await command_error_webhook.send(embed=embed, username = "PotatoBot - Error Logger")

async def error(self, event_method, *args, **kwargs):
    async with aiohttp.ClientSession() as session:
        error_webhook = Webhook.from_url(config["error_webhooks"], session=session)

        embed = discord.Embed(
            title="An error occurred!",
            description=f"```{traceback.format_exc().replace('```', '``')}```",
            color=discord.Color.red()
        )

        embed.add_field(
            name="Event Method",
            value=f"`{event_method}`",
            inline=False
        )

        if args:
            if isinstance(args[0], discord.ext.commands.Context):
                apply_context_errors(embed, args[0], ignore_message=True)
            else:
                embed.add_field(
                    name="Args",
                    value=f"```{args}```",
                    inline=False
                )

        embed.add_field(
            name="Kwargs",
            value=f"```{kwargs}```",
            inline=False
        )

        await error_webhook.send(embed=embed, username="PotatoBot - Error Logger")
