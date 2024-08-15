# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon

import discord

from utils import DBClient
client = DBClient.client
db = client.potatobot

async def send_log(title: str, guild: discord.Guild, description: str, color: discord.Color, channel: discord.TextChannel) -> None:
    c = db["guilds"]

    g = c.find_one({"id": guild.id})

    if not g:
        await channel.send("**Log channel not found! If you are an admin use `/setting log_channel #channel`**")
        return

    if not g["log_channel"]:
        await channel.send("**Log channel not found! If you are an admin use `/setting log_channel #channel`**")
        return

    log_channel = g["log_channel"]
    log_channel = guild.get_channel(log_channel)

    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    await log_channel.send(embed=embed)
