# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon

import random
import os
import aiohttp
import time
import asyncpraw
import inspect
import json
import sys

from asteval import Interpreter
aeval = Interpreter()

import logging
logger = logging.getLogger("discord_bot")

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

from deep_translator import GoogleTranslator

from utils import DBClient, Checks
from ui import translate

db = DBClient.db

reddit = asyncpraw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent="PotatoBot",
)

if not os.path.isfile(f"./config.json"):
    sys.exit("'config.json' not found! Please add it and try again.")
else:
    with open(f"./config.json") as file:
        config = json.load(file)

class General(commands.Cog, name="⬜ General"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.context_menu_message = app_commands.ContextMenu(
            name="Remove spoilers", callback=self.ctx_remove_spoilers
        )
        self.context_menu_message = app_commands.ContextMenu(
            name="Translate",
            callback=self.ctx_translate,
            allowed_contexts=app_commands.AppCommandContext(guild=True, dm_channel=True, private_channel=True),
            allowed_installs=app_commands.AppInstallationType(guild=True, user=True)
        )
        self.bot.tree.add_command(self.context_menu_message)
        self.get_prefix = bot.get_prefix

    # Message context menu command
    async def ctx_remove_spoilers(
        self, interaction: discord.Interaction, message: discord.Message
    ) -> None:
        spoiler_attachment = None
        for attachment in message.attachments:
            if attachment.is_spoiler():
                spoiler_attachment = attachment
                break
        embed = discord.Embed(
            title="Message without spoilers",
            description=message.content.replace("||", ""),
            color=0xBEBEFE,
        )
        if spoiler_attachment is not None:
            embed.set_image(url=attachment.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def ctx_translate(
        self, interaction: discord.Interaction, message: discord.Message
    ) -> None:
        if message.content:
            await interaction.response.send_modal(translate.TranslateModal(message))
        else:
            await interaction.response.send_message("No text to translate", ephemeral=True)

    @commands.hybrid_command(
        name="help",
        aliases=["h", "commands", "cmds"],
        description="Get help with commands",
        usage="help [optional: command]"
    )
    @commands.check(Checks.is_not_blacklisted)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def help(self, context: Context, *, command: str = "none") -> None:
        if command != "none":
            cmd = self.bot.get_command(command)
            if cmd is None:
                await context.send("Command not found")
                return

            if cmd.cog_name == "owner" and not context.author.id in self.bot.owner_ids:
                await context.send("Command not found")
                return

            embed = discord.Embed(
                title=f"Command: {cmd.name}",
                description=cmd.description,
                color=0xBEBEFE
            )

            usage = cmd.usage if cmd.usage else "Not Found"
            example = cmd.extras["example"] if "example" in cmd.extras else "Not Found"
            embed.add_field(
                name="Usage",
                value=f"```Syntax: {usage}\nExample: {example}```",
                inline=False
            )

            aliases = ", ".join(cmd.aliases) if cmd.aliases else "None"
            embed.add_field(
                name="Aliases",
                value=f"```{aliases}```",
                inline=True
            )

            embed.add_field(
                name="Category",
                value=f"```{cmd.cog_name}```",
                inline=True
            )

            cmd_type = ""

            if isinstance(cmd, commands.HybridGroup):
                cmd_type = "Command Group"
            elif isinstance(cmd, commands.HybridCommand):
                cmd_type = "Chat+Slash Command"
            elif isinstance(cmd, commands.Command):
                cmd_type = "Chat Only Command"


            embed.add_field(
                name="Type",
                value=f"```{cmd_type}```",
                inline=True
            )

            params = inspect.signature(cmd.callback).parameters
            param_list = []
            for name, param in params.items():
                if name not in ["self", "context"]:
                    if param.default == inspect.Parameter.empty:
                        param_list.append(f"{name}: <Required>")
                    else:
                        param_list.append(f"{name}: [Optional, default: '{param.default}']")

            params_str = "\n".join(param_list) if param_list else "None"
            embed.add_field(
                name="Parameters",
                value=f"```{params_str}```",
                inline=False
            )

            if isinstance(cmd, commands.HybridGroup):
                    subcommands = ", ".join([sub.name for sub in cmd.commands])
                    embed.add_field(
                        name="Subcommands",
                        value=f"```{subcommands}```",
                        inline=False
                    )

            return await context.send(embed=embed)

        cogs = []

        for cog in self.bot.cogs:
            if cog.startswith("-"):
                continue

            if "owner" in cog and context.author.id != int(os.getenv("OWNER_ID")):
                continue

            if "staff" in cog:
                author_permissions = context.author.guild_permissions

            cogs.append(cog)

        view = CogSelectView(cogs, context.author)

        await context.send('Pick a cog:', view=view)

    @commands.command(
        name="uptime",
        description="Get the bot's uptime",
        usage="uptime"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    async def uptime(self, context: Context):
        uptime = time.time() - self.bot.start_time
        str = time.strftime("%H:%M:%S", time.gmtime(uptime))
        await context.send("Uptime: " + str)

    @commands.hybrid_command(
        name="botinfo",
        description="See bot info",
        usage="botinfo"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def botinfo(self, context: Context) -> None:
        dpyVersion = discord.__version__
        serverCount = len(self.bot.guilds)
        memberCount = len(set(self.bot.get_all_members()))

        shard_id = context.guild.shard_id if context.guild else None
        shard = self.bot.get_shard(shard_id) if shard_id is not None else self.bot.shards[0]
        shard_ping = shard.latency
        shard_servers = len([guild for guild in self.bot.guilds if guild.shard_id == shard_id])
        shard_count = len(self.bot.shards)

        embed = discord.Embed(title=f'{self.bot.user.name} - Stats', color = discord.Color.blurple())

        command_count = len([command for command in self.bot.walk_commands()])

        embed.add_field(name="Bot Version:", value=self.bot.version)
        embed.add_field(name="Discord.Py Version:", value=dpyVersion)
        embed.add_field(name="Ping:", value=f"{round(self.bot.latency * 1000)}ms")
        embed.add_field(name="Total Guilds:", value=serverCount)
        embed.add_field(name="Total Users:", value=memberCount)
        embed.add_field(name="Total Commands:", value=command_count)
        embed.add_field(name="Shard ID:", value=shard_id)
        embed.add_field(name="Shard Ping:", value=f"{round(shard_ping * 1000)}ms")
        embed.add_field(name="Shard Servers:", value=shard_servers)
        embed.add_field(name="Shard Count:", value=shard_count)

        embed.set_footer(text="Bot made by Cyteon @ https://github.com/cyteon")
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="ping",
        description="Check if the bot is alive.",
        usage="ping"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def ping(self, context: Context) -> None:
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"The bot latency is {round(self.bot.latency * 1000)}ms.",
            color=0xBEBEFE,
        )
        await context.send(embed=embed)


    @commands.hybrid_command(
        name="bug",
        description="Send a bug report",
        usage="bug <bug>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.cooldown(5, 3600, commands.BucketType.user)
    async def bug(self, context: Context, *, bug: str) -> None:
        id = int(config["bug_channel"])
        channel = self.bot.get_channel(id)
        embed = discord.Embed(
        	title="Bug Report",
            description=bug,
            color=0xFF0000
        )

        embed.set_footer(text=f"By {context.author} ({context.author.id}) in {context.guild} ({context.guild.id})")

        await channel.send(embed=embed)
        await context.send("Bug Reported")

    @commands.hybrid_command(
        name="translate",
        description="Translate text to a specified language example: ;translate 'How are you' es",
        usage="translate <text> <language>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @app_commands.describe(text="The text you want to translate.")
    @app_commands.describe(language="The language you want to translate the text to.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def translate(self, context: Context, text: str, language: str = "en") -> None:

        translated = GoogleTranslator(source='auto', target=language).translate(text)

        embed = discord.Embed(
            title="Translation",
            description=f"**Original text:**\n{text}\n\n**Translated text:**\n{translated}",
            color=0xBEBEFE,
        )
        embed.set_footer(text=f"Translated to {language}")
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="8ball",
        description="Ask any question to the bot.",
        usage="8ball <question>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @app_commands.describe(question="The question you want to ask.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def eight_ball(self, context: Context, *, question: str) -> None:
        answers = [
            "It is certain.",
            "It is decidedly so.",
            "You may rely on it.",
            "Without a doubt.",
            "Yes - definitely.",
            "As I see, yes.",
            "Most likely.",
            "Outlook good.",
            "Yes.",
            "Signs point to yes.",
            "Reply hazy, try again.",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again later.",
            "Don't count on it.",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good.",
            "Very doubtful.",
            "Potato"
        ]
        embed = discord.Embed(
            title="**My Answer:**",
            description=f"{random.choice(answers)}",
            color=0xBEBEFE,
        )
        embed.set_footer(text=f"The question was: {question}")
        await context.send(embed=embed)

    @commands.command(
        name="support",
        description="Support Server.",
        usage="support"
    )
    @commands.check(Checks.command_not_disabled)
    async def support(self, context: commands.Context) -> None:
        message = await context.send("https://discord.gg/wtur9j8uVP")

    @commands.hybrid_command(
        name="urban-dictionary",
        description="Get the definition of a word from Urban Dictionary.",
        usage="urban-dictionary <word>",
        aliases=["urban"]
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def urban_dict(self, context: Context, *, term: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.urbandictionary.com/v0/define?term={term}") as response:
                data = await response.json()

                if not data["list"]:
                    return await context.send("No results found.")

                definition = data["list"][0]["definition"]

                embed = discord.Embed(
                    title=f"Definition of {term}",
                    description=definition,
                    color=0xBEBEFE
                )

                await context.send(embed=embed)

    @commands.hybrid_command(
        name="reddit",
        description="Returns a random post from reddit, or from a subreddit",
        usage="reddit [optional: subreddit]"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def reddit(self, context: Context, subreddit: str = "") -> None:
        if subreddit == "":
            subreddit = await reddit.subreddit("random")
        else:
            subreddit = await reddit.subreddit(subreddit)

        #check if NSFW
        loaded_sub = subreddit
        await loaded_sub.load()

        if hasattr(context.channel, "over18"):
            if loaded_sub.over18 and not context.channel.is_nsfw() and not context.channel.id == context.author.id:
                await context.send("This subreddit is NSFW, please use this command in a NSFW channel or dms.")
                return

        posts = []
        async for post in subreddit.hot(limit=25):
            posts.append(post)

        random_post = None

        if len(posts) == 0:
            return await context.send("No posts found")

        while True:
            if len(posts) == 0:
                await context.send("No posts that are not NSFW found, try again or run command in an NSFW channel or dms.")
                return

            random_post = random.choice(posts)
            posts.remove(random_post)

            loaded_post = random_post
            await loaded_post.load()

            if not context.guild:
                if loaded_post.over_18 and not context.channel.is_nsfw() and not context.channel.id == context.author.id:
                    continue

            if loaded_post.stickied:
                continue

            break

        logger.info(f"Reddit post: {random_post.url}")

        title = random_post.title
        url = random_post.url
        author = random_post.author

        embed = discord.Embed(
            title=title,
            description=random_post.selftext,
            url=url,
            color=0xBEBEFE,
        )

        if random_post.url.endswith(('.jpg', '.jpeg', '.png', '.gif')):
            embed.set_image(url=random_post.url)

        await context.send(embed=embed)

    @commands.hybrid_command(
        name="vote",
        description="Vote for the bot on top.gg",
        usage="vote"
    )
    @commands.check(Checks.command_not_disabled)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def vote(self, context: Context):
        embed = discord.Embed(
            title="Vote on top.gg",
            description="Help out the bot by voting now!",
            url="https://top.gg/bot/1226487228914602005/vote",
            color=0xBEBEFE
        )

        await context.send(embed=embed, view=VoteView())

    @commands.hybrid_command(
        name="calc",
        description="Calculate a math expression.",
        usage="calc <expression>",
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def calc(self, context: Context, *, expression: str) -> None:
        try:
            result = aeval(expression)

            embed = discord.Embed(
                title="Calculator",
                description=f"**Input:**\n```{expression}```\n**Output:**\n```{result}```",
                color=0xBEBEFE
            )

            await context.send(embed=embed)
        except Exception as e:
            await context.send(f"An error occurred: {e}")

class VoteButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.link, label="Vote on top.gg", url="https://top.gg/bot/1226487228914602005/vote")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Thank you for voting!", ephemeral=True)

class VoteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(VoteButton())

class CogSelect(discord.ui.Select):
    def __init__(self, cogs, author):
        options = [
            discord.SelectOption(label=cog, description=f"Show commands for {cog}")
            for cog in cogs
        ]
        super().__init__(placeholder='Choose a cog...', min_values=1, max_values=1, options=options)
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("You cannot use this select.", ephemeral=True)
            return

        await interaction.response.defer()

        cog_name = self.values[0]
        cog = interaction.client.get_cog(cog_name)
        commands = cog.get_commands()
        data = []
        for command in commands:
            description = command.description.partition("\n")[0]
            data.append(f"{await interaction.client.get_prefix(interaction)}{command.name} - {description}")
        help_text = "\n".join(data)
        embed = discord.Embed(
            title=f"Help: {cog_name}", description="List of available commands:", color=0xBEBEFE
        )
        embed.add_field(
            name=cog_name.capitalize(), value=f"```{help_text}```", inline=False
        )
        embed.set_footer(text=f"To get more info on a command, use {await interaction.client.get_prefix(interaction)}help <command>")

        # Edit the original message instead of sending a new one
        await interaction.message.edit(embed=embed)

class CogSelectView(discord.ui.View):
    def __init__(self, cogs, author):
        super().__init__(timeout=None)
        self.add_item(CogSelect(cogs, author))

async def setup(bot) -> None:
    await bot.add_cog(General(bot))
    bot.add_view(VoteView())
