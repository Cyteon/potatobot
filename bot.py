# pylint: disable-all

# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon

import json
import logging
import os
import platform
import random
import sys
import time
import aiohttp
import threading
from fastapi import FastAPI
import uvicorn

import pickledb
import pymongo

import discord
from discord import Webhook
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()

import utils
from utils import CONSTANTS, CachedDB, ErrorLogger

if not os.path.isfile(f"{os.path.realpath(os.path.dirname(__file__))}/config.json"):
    sys.exit("'config.json' not found! Please add it and try again.")
else:
    with open(f"{os.path.realpath(os.path.dirname(__file__))}/config.json") as file:
        config = json.load(file)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = pymongo.MongoClient(os.getenv("MONGODB_URL"))
db = client.potatobot

os.makedirs("pickle", exist_ok=True)
prefixDB = pickledb.load("pickle/prefix.db", False)
statsDB = pickledb.load("pickle/stats.db", False)

class LoggingFormatter(logging.Formatter):
    black = "\x1b[30m"
    red = "\x1b[31m"
    green = "\x1b[32m"
    yellow = "\x1b[33m"
    blue = "\x1b[34m"
    gray = "\x1b[38m"
    reset = "\x1b[0m"
    bold = "\x1b[1m"

    COLORS = {
        logging.DEBUG: gray + bold,
        logging.INFO: blue + bold,
        logging.WARNING: yellow + bold,
        logging.ERROR: red,
        logging.CRITICAL: red + bold,
    }

    def format(self, record):
        log_color = self.COLORS[record.levelno]
        format = "(black){asctime}(reset) (levelcolor){levelname:<8}(reset) \x1b[32m{name}(reset) {message}"
        format = format.replace("(black)", self.black + self.bold)
        format = format.replace("(reset)", self.reset)
        format = format.replace("(levelcolor)", log_color)
        formatter = logging.Formatter(format, "%Y-%m-%d %H:%M:%S", style="{")
        return formatter.format(record)

logger = logging.getLogger("discord_bot")
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(LoggingFormatter())
file_handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
file_handler_formatter = logging.Formatter(
    "[{asctime}] [{levelname:<8}] {name}: {message}", "%Y-%m-%d %H:%M:%S", style="{"
)
file_handler.setFormatter(file_handler_formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

class DiscordBot(commands.AutoShardedBot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix=self.get_prefix,
            intents=intents,
            help_command=None,
            owner_ids=set([int(os.getenv("OWNER_ID")), 1131236182899052696]),
        )
        self.logger = logger
        self.config = config
        self.version = "2.0.0-beta"
        self.start_time = time.time()
        self.prefixDB = prefixDB
        self.statsDB = statsDB

    async def get_prefix(self, message):
        guild_id = str(message.guild.id)
        if prefixDB.exists(guild_id):
            return prefixDB.get(guild_id)
        else:
            return config["prefix"]

    async def load_cogs(self) -> None:
        for file in os.listdir(f"{os.path.realpath(os.path.dirname(__file__))}/cogs"):
            if file.endswith(".py"):
                extension = file[:-3]
                try:
                    await self.load_extension(f"cogs.{extension}")
                    self.logger.info(f"Loaded extension '{extension}'")
                except Exception as e:
                    exception = f"{type(e).__name__}: {e}"
                    self.logger.error(
                        f"Failed to load extension {extension}\n{exception}"
                    )

    @tasks.loop(minutes=1.0)
    async def status_task(self) -> None:
        statuses = ["youtube", "netflix"]
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=random.choice(statuses)))

    @status_task.before_loop
    async def before_status_task(self) -> None:
        await self.wait_until_ready()


    async def setup_hook(self) -> None:
        self.logger.info(f"Logged in as {self.user.name}")
        self.logger.info(f"discord.py API version: {discord.__version__}")
        self.logger.info(f"Python version: {platform.python_version()}")
        self.logger.info(
            f"Running on: {platform.system()} {platform.release()} ({os.name})"
        )

        self.logger.info("-------------------")

        self.logger.info(f"Connection to db successful: {client.address}")

        self.logger.info("-------------------")

        await self.load_cogs()

        self.logger.info("-------------------")

        self.logger.info(f"Command count (slash+chat): {len([x for x in self.walk_commands() if isinstance(x, commands.HybridCommand)])}")
        self.logger.info(f"Command count (chat only): {len([x for x in self.walk_commands() if isinstance(x, commands.Command) and not isinstance(x, commands.HybridCommand)])}")
        self.logger.info(f"Total command count: {len([x for x in self.walk_commands()])}")

        self.logger.info(
            f"Command groups: {len([x for x in self.walk_commands() if isinstance(x, commands.HybridGroup) or isinstance(x, commands.Group)])}"
        )
        self.logger.info(f"Cog count: {len([x for x in self.cogs])}")

        self.logger.info(
            f"Discord slash command limit: {len([x for x in self.commands if isinstance(x, commands.HybridCommand) or isinstance(x, commands.HybridGroup)])}/100"
        )
        self.logger.info("(Dosent include subcommands)")

        self.logger.info("-------------------")

        self.status_task.start()

    async def on_guild_remove(self, guild: discord.Guild):
        async with aiohttp.ClientSession() as session:
            to_send = Webhook.from_url(config["join_leave_webhooks"], session=session)

            embed = discord.Embed(
                title="Bot left a guild!",
                description=f"**Guild Name:** {guild.name}\n**Guild ID:** {guild.id}\n**Owner:** {guild.owner.mention if guild.owner else None} ({guild.owner})\n **Member Count:** {guild.member_count}",
                color=0xE02B2B
            )

            await to_send.send(embed=embed, username="PotatoBot - Guild Logger")

        self.logger.info("Bot left guild " + guild.name)

    async def on_guild_join(self, guild: discord.Guild):
        async with aiohttp.ClientSession() as session:
            to_send = Webhook.from_url(config["join_leave_webhooks"], session=session)

            embed = discord.Embed(
                title="Bot joined a guild!",
                description=f"**Guild Name:** {guild.name}\n**Guild ID:** {guild.id}\n**Owner:** {guild.owner.mention if guild.owner else None} ({guild.owner})\n **Member Count:** {guild.member_count}",
                color=0x57F287
            )

            await to_send.send(embed=embed, username="PotatoBot - Guild Logger")

        self.logger.info("Bot joined guild: " + guild.name)

    async def on_error(self, event_method, *args, **kwargs):
        await ErrorLogger.error(self, event_method, *args, **kwargs)

    async def on_message(self, message: discord.Message) -> None:
        if message.author.id in config["fully_ignore"]:
            return

        if message.author == self.user or message.author.bot:
            return

        arr = message.content.split(" ")

        arr[0] = arr[0].lower()

        message.content = " ".join(arr)

        ctx = await self.get_context(message)
        if ctx.command is not None:
            self.dispatch('command', ctx)
            try:
                if await self.can_run(ctx, call_once=True):
                    await ctx.command.invoke(ctx)
                else:
                    raise commands.errors.CheckFailure('The global check once functions failed.')
            except commands.errors.CommandError as exc:
                await ctx.command.dispatch_error(ctx, exc)
            else:
                self.dispatch('command_completion', ctx)
        elif ctx.invoked_with:
            exc = commands.errors.CommandNotFound(f'Command "{ctx.invoked_with}" is not found')
            self.dispatch('command_error', ctx, exc)
        else:
            if f"<@{str(self.user.id)}>" in message.content:
                await message.reply(f"> My prefix is `{await self.get_prefix(message)}`")


    async def on_command_completion(self, context: commands.Context) -> None:
        full_command_name = context.command.qualified_name
        split = full_command_name.split(" ")
        executed_command = str(split[0])

        if context.guild is not None:
            self.logger.info(
                f"Executed {executed_command} command in {context.guild.name} (ID: {context.guild.id}) by {context.author} (ID: {context.author.id})"
            )
        else:
            self.logger.info(
                f"Executed {executed_command} command by {context.author} (ID: {context.author.id}) in DMs"
            )

        commands_ran = (statsDB.get("commands_ran") if statsDB.exists("commands_ran") else 0) + 1
        statsDB.set("commands_ran", commands_ran)
        statsDB.dump()

    async def on_command_error(self, context: commands.Context, error) -> None:
        if isinstance(error, commands.CommandOnCooldown):
            minutes, seconds = divmod(error.retry_after, 60)
            hours, minutes = divmod(minutes, 60)
            hours = hours % 24
            embed = discord.Embed(
                description=f"**Please slow down** - You can use this command again in {f'{round(hours)} hours' if round(hours) > 0 else ''} {f'{round(minutes)} minutes' if round(minutes) > 0 else ''} {f'{round(seconds)} seconds' if round(seconds) > 0 else ''}.",
                color=0xE02B2B,
            )
            await context.send(embed=embed)
        elif isinstance(error, commands.NotOwner):
            embed = discord.Embed(
                description="You are not the owner of the bot!", color=0xE02B2B
            )
            await context.send(embed=embed)
            if context.guild:
                self.logger.warning(
                    f"{context.author} (ID: {context.author.id}) tried to execute an owner only command in the guild {context.guild.name} (ID: {context.guild.id}), but the user is not an owner of the bot."
                )
            else:
                self.logger.warning(
                    f"{context.author} (ID: {context.author.id}) tried to execute an owner only command in the bot's DMs, but the user is not an owner of the bot."
                )
        elif isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                description="You are missing the permission(s) `"
                + ", ".join(error.missing_permissions)
                + "` to execute this command!",
                color=0xE02B2B,
            )
            await context.send(embed=embed)
        elif isinstance(error, commands.BotMissingPermissions):
            embed = discord.Embed(
                description="I am missing the permission(s) `"
                + ", ".join(error.missing_permissions)
                + "` to fully perform this command!",
                color=0xE02B2B,
            )
            await context.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="Error!",
                description=str(error).capitalize(),
                color=0xE02B2B,
            )
            await context.send(embed=embed)
        elif isinstance(error, commands.CheckFailure):
            embed = discord.Embed(
                title="Error!",
                description=str(error).capitalize(),
                color=0xE02B2B,
            )
            await context.send(embed=embed)
        elif isinstance(error, commands.CommandNotFound):
            embed = discord.Embed(
                title = "Command not Found!",
                description=str(error).capitalize(),
                color=0xE02B2B
            )

            await context.send(embed=embed)
        elif isinstance(error, commands.CommandError):
            embed = discord.Embed(
                title="Error!",
                description=str(error).capitalize(),
                color=0xE02B2B,
            )
            await context.send(embed=embed)

            await ErrorLogger.command_error(error, context)
        else:
            if "not found" in str(error):
                embed = discord.Embed(
                    title="Error!",
                    description=str(error).capitalize(),
                    color=0xE02B2B,
                )
                await context.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="Error!",
                    description=str(error).capitalize(),
                    color=0xE02B2B,
                )
                await context.send(embed=embed)
                await ErrorLogger.command_error(error, context)
                raise error
