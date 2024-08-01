# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon

import discord
import asyncio
import ast
import inspect
import traceback
import os
import sys
import pymongo
from datetime import datetime


from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

import contextlib
import io

from utils import CONSTANTS, DBClient, Checks, ErrorLogger, CachedDB

client = DBClient.client
db = client.potatobot

def insert_returns(body):
    # insert return stmt if the last expression is a expression statement
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])

    # for if statements, we insert returns into the body and the orelse
    if isinstance(body[-1], ast.If):
        insert_returns(body[-1].body)
        insert_returns(body[-1].orelse)

    # for with blocks, again we insert returns into the body
    if isinstance(body[-1], ast.With):
        insert_returns(body[-1].body)

class Owner(commands.Cog, name="owner"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.command(
        name="test-error",
        description="Test error handling",
        usage="test-error <message>",
    )
    @commands.is_owner()
    async def test_error(self, context: Context, *, message: str) -> None:
        raise Exception(message)

    @commands.command(
        name="sync",
        description="Sync the slash commands.",
        usage="sync guild/global"
    )
    @app_commands.describe(scope="The scope of the sync. Can be `global` or `guild`")
    @commands.is_owner()
    async def sync(self, context: Context, scope: str) -> None:
        if scope == "global":
            await context.bot.tree.sync()
            embed = discord.Embed(
                description="Slash commands have been globally synchronized.",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
            return
        elif scope == "guild":
            context.bot.tree.copy_global_to(guild=context.guild)
            await context.bot.tree.sync(guild=context.guild)
            embed = discord.Embed(
                description="Slash commands have been synchronized in this guild.",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description="The scope must be `global` or `guild`.", color=0xE02B2B
        )
        await context.send(embed=embed)

    @commands.command(
        name="unsync",
        description="Unsync the slash commands",
        usage="unsync guild/global"
    )
    @commands.is_owner()
    async def unsync(self, context: Context, scope: str) -> None:
        if scope == "global":
            context.bot.tree.clear_commands(guild=None)
            await context.bot.tree.sync()
            embed = discord.Embed(
                description="Slash commands have been globally unsynchronized.",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
            return
        elif scope == "guild":
            context.bot.tree.clear_commands(guild=context.guild)
            await context.bot.tree.sync(guild=context.guild)
            embed = discord.Embed(
                description="Slash commands have been unsynchronized in this guild.",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description="The scope must be `global` or `guild`.", color=0xE02B2B
        )
        await context.send(embed=embed)

    @commands.command(
        name="sudo",
        description="sus",
        usage="sudo <user> <command> [args...]",
    )
    @commands.is_owner()
    async def sudo(self, context: Context, user: discord.Member, *, command: str) -> None:
        message = context.message
        message.author = user
        message.content = context.prefix + command
        await self.bot.process_commands(message)

    @commands.hybrid_command(
        name="load",
        description="Load a cog",
        usage="load <cog>",
    )
    @commands.is_owner()
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def load(self, context: Context, cog: str) -> None:
        try:
            await self.bot.load_extension(f"cogs.{cog}")
        except Exception:
            embed = discord.Embed(
                description=f"Could not load the `{cog}` cog.", color=0xE02B2B
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description=f"Successfully loaded the `{cog}` cog.", color=0xBEBEFE
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="unload",
        description="Unloads a cog.",
        usage="unload <cog>",
    )
    @commands.is_owner()
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def unload(self, context: Context, cog: str) -> None:
        try:
            await self.bot.unload_extension(f"cogs.{cog}")
        except Exception:
            embed = discord.Embed(
                description=f"Could not unload the `{cog}` cog.", color=0xE02B2B
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description=f"Successfully unloaded the `{cog}` cog.", color=0xBEBEFE
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="reload",
        description="Reloads a cog",
        usage="reload <cog>",
    )
    @app_commands.describe(cog="The name of the cog to reload")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.is_owner()
    async def reload(self, context: Context, cog: str) -> None:
        try:
            await self.bot.reload_extension(f"cogs.{cog}")
        except Exception:
            embed = discord.Embed(
                description=f"Could not reload the `{cog}` cog.", color=0xE02B2B
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description=f"Successfully reloaded the `{cog}` cog.", color=0xBEBEFE
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="shutdown",
        description="bye",
        usage="shutdown"
    )
    @commands.is_owner()
    async def shutdown(self, context: Context) -> None:
        embed = discord.Embed(description="Shutting down. Bye! :wave:", color=0xBEBEFE)
        await context.send(embed=embed)
        sys.exit(0)

    @commands.hybrid_command(
        name="say",
        description="talk",
        usage="say <message>",
    )
    @commands.is_owner()
    async def say(self, context: Context, *, message: str) -> None:
        await context.channel.send(message)

    @commands.hybrid_command(
        name="embed",
        description="say smth in embed",
    )
    @commands.is_owner()
    async def embed(self, context: Context, title: str, description: str, footer: str = "") -> None:
        embed = discord.Embed(
            title=title, description=description, color=0xBEBEFE
        )

        embed.set_footer(text=footer)

        await context.channel.send(embed=embed)

    @commands.command(
        name="reply",
        description="Reply to a message",
        usage="reply <channel_id> <message_id> <reply>",
    )
    @commands.is_owner()
    async def reply(self, context: Context, channel_id: int, message_id: int, *, reply: str) -> None:
        channel = self.bot.get_channel(channel_id)
        message = await channel.fetch_message(message_id)
        await message.reply(reply)

    @commands.hybrid_command(
        name="eval",
        description=":D",
        usage="eval <code>",
    )
    @commands.is_owner()
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def eval(self, context, *, cmd: str):
        fn_name = "_eval_expr"

        cmd = cmd.strip("` ")

        # add a layer of indentation
        cmd = "\n".join(f"    {i}" for i in cmd.splitlines())

        # wrap in async def body
        body = f"async def {fn_name}():\n{cmd}"

        parsed = ast.parse(body)
        body = parsed.body[0].body

        insert_returns(body)

        env = {
            'bot': context.bot,
            'discord': discord,
            'commands': commands,
            'context': context,
            'db': db,
            '__import__': __import__
        }
        exec(compile(parsed, filename="<ast>", mode="exec"), env)

        result = (await eval(f"{fn_name}()", env))
        await context.send(result)


    @commands.command(
        name="enable_ai",
        description="Give server AI access",
        usage="enable_ai [optional: server id]",
    )
    @commands.is_owner()
    async def enable_ai(self, context, server: int = 0):
        c = db["guilds"]

        data = c.find_one(
            {
                "id": server if server != 0 else context.guild.id
            }
        )

        if not data:
            data = CONSTANTS.guild_data_template(context.guild.id)
            c.insert_one(data)

        newdata = { "$set": { "ai_access": True } }

        c.update_one({"id": context.guild.id}, newdata)

        await context.send("AI access have been enabled in this server")

    @commands.command(
        name="disable_ai",
        description="Disable server AI access",
        usage="disable_ai [optional: server id]",
    )
    @commands.is_owner()
    async def disable_ai(self, context, server_id: int = 0):

        c = db["guilds"]

        data = c.find_one(
            {
                "id": server_id if server_id != 0 else context.guild.id
            }
        )

        if not data:
            data = CONSTANTS.guild_data_template(context.guild.id)
            c.insert_one(data)

        newdata = { "$set": { "ai_access": False } }

        c.update_one({"id": context.guild.id}, newdata)

        await context.send("AI access have been disabled in this server")

    @commands.hybrid_command(
        name="blacklist",
        description="Blacklist a user",
        usage="blacklist <user> [reason: optional]",
    )
    @commands.is_owner()
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def blacklist(self, context, user: discord.User, *, reason: str = "No reason provided"):
        users_global = db["users_global"]
        user_data = users_global.find_one({"id": user.id})

        if user is None:
            user_data = CONSTANTS.user_global_data_template(user.id)
            users_global.insert_one(user_data)

        newdata = {
            "$set": {
                "blacklisted": True,
                "blacklist_reason": reason
            }
        }

        await CachedDB.update_one(users_global, {"id": user.id}, newdata)

        await context.send(f"{user} has been blacklisted.")

        embed = discord.Embed(
            title=f"You have been blacklisted from using the bot",
            color=0xE02B2B,
            description=f"Reason: {reason}"
        )

        try:
            await user.send(embed=embed)
        except Exception as e:
            await context.send(f"Could not send message to {user.mention} due to: {e}")

    @commands.hybrid_command(
        name="unblacklist",
        description="Unblacklist a user",
        usage="unblacklist <user>",
    )
    @commands.is_owner()
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def unblacklist(self, context, user: discord.User):
        users_global = db["users_global"]
        user_data = users_global.find_one({"id": user.id})

        if user_data is None:
            user_data = CONSTANTS.user_global_data_template(user.id)
            users_global.insert_one(user_data)

        newdata = {
            "$set": {
                "blacklisted": False,
                "blacklist_reason": ""
            }
        }

        await CachedDB.update_one(users_global, {"id": user.id}, newdata)

        await context.send(f"{user} has been unblacklisted.")

        embed = discord.Embed(
            title=f"You have been unblacklisted from using the bot",
            color=0xBEBEFE,
        )

        try:
            await user.send(embed=embed)
        except Exception as e:
            await context.send(f"Could not send message to {user.mention} due to: {e}")

    @commands.hybrid_command(
        name="ai-ignore",
        description="Make the AI ignore someone",
        usage="ai_ignore <user> [reason: optional]",
    )
    @commands.is_owner()
    async def ai_ignore(self, context, user: discord.User, *, reason: str = "No reason provided"):
        users_global = db["users_global"]
        user_data = users_global.find_one({"id": user.id})

        if user_data is None:
            user_data = CONSTANTS.user_global_data_template(user.id)
            user_data.insert_one(user_data)

        newdata = {
            "$set": {
                "ai_ignore": True,
                "ai_ignore_reason": reason
            }
        }

        await CachedDB.update_one(users_global, {"id": user.id}, newdata)

        await context.send(f"{user} will now be ignored by the AI.")

    @commands.hybrid_command(
        name="ai-unignore",
        description="Make the AI not ignore someone",
        usage="ai-unignore <user>",
    )
    @commands.is_owner()
    async def ai_unignore(self, context, user: discord.User):
        users_global = db["users_global"]
        user_data = users_global.find_one({"id": user.id})

        if user_data is None:
            user_data = CONSTANTS.user_global_data_template(user.id)
            users_global.insert_one(user_data)

        newdata = {
            "$set": {
                "ai_ignore": False,
                "ai_ignore_reason": ""
            }
        }

        await CachedDB.update_one(users_global, {"id": user.id}, newdata)

        await context.send(f"{user} will no longer be ignored by the AI")

    @commands.command(
        name="inspect",
        description="Inspect a user",
        usage="inspect <user>",
    )
    @commands.is_owner()
    async def inspect(self, context, user: discord.User):
        users_global = db["users_global"]
        user_data = users_global.find_one({"id": user.id})

        if user_data is None:
            user_data = CONSTANTS.user_global_data_template(user.id)
            users_global.insert_one(user_data)

        embed = discord.Embed(
            title=f"Inspecting {user}",
            color=0xBEBEFE
        )

        embed.add_field(name="Total Commands", value=user_data["inspect"]["total_commands"])
        embed.add_field(name="Times Flagged", value=user_data["inspect"]["times_flagged"])
        embed.add_field(name="NSFW Requests", value=user_data["inspect"]["nsfw_requests"])

        # STUFF THAT MIGHT NOT BE FOUND
        if "ai_requests" in user_data["inspect"]:
            embed.add_field(name="AI Requests", value=user_data["inspect"]["ai_requests"])

        if user_data["blacklisted"]:
            embed.add_field(name="Blacklist Reason", value=user_data["blacklist_reason"])

        if user_data["ai_ignore"]:
            embed.add_field(name="AI Ignore Reason", value=user_data["ai_ignore_reason"])

        await context.send(embed=embed)

    @commands.command(
    	name="inspect-clear",
        description="Clear someones inspect data",
        usage="inspect-clear <user>",
    )
    @commands.is_owner()
    async def inspect_clear(self, context: Context, user: discord.Member):
        users_global = db["users_global"]

        newdata = {
            "$set": {"inspect.total_commands": 0, "inspect.times_flagged": 0, "inspect.nsfw_requests": 0, "inspect.ai_requests": 0}
        }

        users_global.update_one({"id": user.id}, newdata)

        user_new = users_global.find_one({"id": user.id})

        await context.send(f"Cleared inspect info for {user.mention}")

    @commands.command(
        name="top-flagged",
        description="Get the top flagged users",
        usage="top-flagged"
    )
    @commands.is_owner()
    async def top_flagged(self, context):
        users_global = db["users_global"]
        users = users_global.find().sort("inspect.times_flagged", -1).limit(10)

        embed = discord.Embed(
            title="Top Flagged Users",
            color=0xBEBEFE
        )

        for user in users:
            discord_user = self.bot.get_user(user["id"])
            if not discord_user:
                continue
            embed.add_field(name=f"{str(discord_user).capitalize()} ({discord_user.id})", value= f"Flagged **{user['inspect']['times_flagged']}** times", inline=False)

        await context.send(embed=embed)

    @commands.command(
        name="top-nsfw",
        description="Get the top NSFW requesters",
        usage="top-nsfw"
    )
    @commands.is_owner()
    async def top_nsfw(self, context):
        users_global = db["users_global"]
        users = users_global.find().sort("inspect.nsfw_requests", -1).limit(10)

        embed = discord.Embed(
            title="Top NSFW Requesters",
            color=0xBEBEFE
        )

        for user in users:
            discord_user = self.bot.get_user(user["id"])
            if not discord_user:
                continue
            embed.add_field(name=f"{str(discord_user).capitalize()} ({discord_user.id})", value= f"**{user['inspect']['nsfw_requests']}** NSFW requests", inline=False)

        await context.send(embed=embed)

    @commands.command(
        name="ai-announce",
        description="Announce smth",
        usage="ai-announce <message>"
    )
    @commands.is_owner()
    async def ai_announce(self, context, *, message: str):
        channels = db["ai_channels"]
        listOfChannels = channels.find_one({"listOfChannels": True})

        embed = discord.Embed(description=message)

        for channel_id in listOfChannels["ai_channels"]:
            channel = self.bot.get_channel(channel_id)
            if channel:

                await channel.send(embed=embed)

    @commands.hybrid_command(
        name="copy-db-to-backup",
        description="Copy the database to a backup",
        usage="copy-db-to-backup"
    )
    @commands.is_owner()
    async def copy_db_to_backup(self, context):
        backup_db = pymongo.MongoClient(os.getenv("MONGODB_BACKUP_URL")).potatobot

        message = await context.send("""
        Status:
            Removing old data: :tools:
            Copying guilds: :x:
            Copying ai_channels: :x:
            Copying users: :x:
            Copying AI convos: :x:
            Copying global user data: :x:
            Copying starboard: :x:
            Copying reaction roles: :x:
        """)

        backup_db["ai_convos"].drop()
        backup_db["guilds"].drop()
        backup_db["ai_channels"].drop()
        backup_db["users"].drop()
        backup_db["starboard"].drop()
        backup_db["users_global"].drop()
        backup_db["reactionroles"].drop()

        for guild in db["guilds"].find():
            backup_db["guilds"].insert_one(guild)

        await message.edit(content="""
        Status:
            Removing old data: :white_check_mark:
            Copying guilds: :tools:
            Copying ai_channels: :x:
            Copying users: :x:
            Copying AI convos: :x:
            Copying global user data: :x:
            Copying starboard: :x:
            Copying reaction roles: :x:
        """)

        await message.edit(content="""
        Status:
            Removing old data: :white_check_mark:
            Copying guilds: :white_check_mark:
            Copying ai_channels: :tools:
            Copying users: :x:
            Copying AI convos: :x:
            Copying global user data: :x:
            Copying starboard: :x:
            Copying reaction roles: :x:
        """)

        for channel in db["ai_channels"].find():
            backup_db["ai_channels"].insert_one(channel)

        await message.edit(content="""
        Status:
            Removing old data: :white_check_mark:
            Copying guilds: :white_check_mark:
            Copying ai_channels: :white_check_mark:
            Copying users: :tools:
            Copying AI convos: :x:
            Copying global user data: :x:
            Copying starboard: :x:
            Copying reaction roles: :x:
        """)

        for user in db["users"].find():
            backup_db["users"].insert_one(user)

        await message.edit(content="""
        Status:
            Removing old data: :white_check_mark:
            Copying guilds: :white_check_mark:
            Copying ai_channels: :white_check_mark:
            Copying users: :white_check_mark:
            Copying AI convos: :tools:
            Copying global user data: :x:
            Copying starboard: :x:
            Copying reaction roles: :x:
        """)

        for convo in db["ai_convos"].find():
            backup_db["ai_convos"].insert_one(convo)

        await message.edit(content="""
        Status:
            Removing old data: :white_check_mark:
            Copying guilds: :white_check_mark:
            Copying ai_channels: :white_check_mark:
            Copying users: :white_check_mark:
            Copying AI convos: :white_check_mark:
            Copying global user data: :tools:
            Copying starboard: :x:
            Copying reaction roles: :x:
        """)

        for user in db["users_global"].find():
            backup_db["users_global"].insert_one(user)

        await message.edit(content="""
        Status:
            Removing old data: :white_check_mark:
            Copying guilds: :white_check_mark:
            Copying ai_channels: :white_check_mark:
            Copying users: :white_check_mark:
            Copying AI convos: :white_check_mark:
            Copying global user data: :white_check_mark:
            Copying starboard: :tools:
            Copying reaction roles: :x:
        """)

        for starboard in db["starboard"].find():
            backup_db["starboard"].insert_one(starboard)

        await message.edit(content="""
        Status:
            Removing old data: :white_check_mark:
            Copying guilds: :white_check_mark:
            Copying ai_channels: :white_check_mark:
            Copying users: :white_check_mark:
            Copying AI convos: :white_check_mark:
            Copying global user data: :white_check_mark:
            Copying starboard: :white_check_mark:
            Copying reaction roles: :tools:
        """)

        for starboard in db["reactionroles"].find():
            backup_db["reactionroles"].insert_one(starboard)

        await message.edit(content="""
        Status:
            Removing old data: :white_check_mark:
            Copying guilds: :white_check_mark:
            Copying ai_channels: :white_check_mark:
            Copying users: :white_check_mark:
            Copying AI convos: :white_check_mark:
            Copying global user data: :white_check_mark:
            Copying starboard: :white_check_mark:
            Copying reaction roles: :white_check_mark:

            **Backup Done!!!**
        """)

    @commands.command(
        name="force_system_prompt",
        description="Set the system prompt for the AI",
    )
    @commands.is_owner()
    async def force_system_prompt(self, context: Context, *, prompt: str) -> None:
        c = db["guilds"]
        data = c.find_one({"id": context.guild.id})

        newdata = {
                "$set": { "system_prompt": prompt }
        }

        c.update_one(
            { "id": context.guild.id }, newdata
        )

        await context.send("System prompt set to: " + prompt)

    @commands.hybrid_group(
        name="strikes",
        description="Stuff for striking users"
    )
    async def strikes(self, context: Context):
        prefix = await self.bot.get_prefix(context)

        cmds = "\n".join([f"{prefix}strikes {cmd.name} - {cmd.description}" for cmd in self.strikes.walk_commands()])

        embed = discord.Embed(
            title=f"Help: Strikes", description="List of available commands:", color=0xBEBEFE
        )
        embed.add_field(
            name="Commands", value=f"```{cmds}```", inline=False
        )

        await context.send(embed=embed)

    @strikes.command(
        name="add",
        description="Strike a user"
    )
    @commands.is_owner()
    async def add(self, context: Context, user: discord.User, *, reason: str):
        users = db["users_global"]
        user_data = users.find_one({"id": user.id})

        if user_data is None:
            user_data = CONSTANTS.user_global_data_template(user.id)
            users.insert_one(user_data)

        if not "strikes" in user_data:
            user_data["strikes"] = []

        user_data["strikes"].append({"reason": reason, "time": datetime.now().strftime("%d.%m.%Y %H:%M:%S")})

        newdata = {"$set": {"strikes": user_data["strikes"]}}

        users.update_one({"id": user.id}, newdata)

        await context.send(f"{user.mention} has been striked for **{reason}** | This is strike {len(user_data['strikes'])}")

        embed = discord.Embed(
            title=f"You have received a global strike",
            color=0xE02B2B,
            description=f"Reason: {reason}"
        )
        embed.set_footer(text="Time: " + datetime.now().strftime("%d.%m.%Y %H:%M:%S"))

        try:
            await user.send(embed=embed)
        except Exception as e:
            await context.send(f"Could not send message to {user.mention} due to: {e}")

    @strikes.command(
        name="remove",
        description="Remove a strike from a user"
    )
    @commands.is_owner()
    async def remove(self, context: Context, user: discord.User, id: int):
        users = db["users_global"]
        user_data = users.find_one({"id": user.id})

        if user_data is None:
            user_data = CONSTANTS.user_global_data_template(user.id)
            users.insert_one(user_data)

        if not "strikes" in user_data:
            user_data["strikes"] = []

        if id > len(user_data["strikes"]):
            await context.send("That strike does not exist")
            return

        reason = user_data["strikes"][id]["reason"]
        user_data["strikes"].pop(id)

        newdata = {"$set": {"strikes": user_data["strikes"]}}

        users.update_one({"id": user.id}, newdata)

        await context.send(f"Strike **{id}** has been removed from {user.mention}")

        embed = discord.Embed(
            title=f"Globally removed strike | ID: {id}",
            color=0xBEBEFE,
            description=f"Reason: {reason}"
        )
        embed.set_footer(text="Time: " + datetime.now().strftime("%d.%m.%Y %H:%M:%S"))

        try:
            await user.send(embed=embed)
        except Exception as e:
            await context.send(f"Could not send message to {user.mention} due to: {e}")

    @strikes.command(
        name="list",
        description="Lists a users strikes"
    )
    @commands.is_owner()
    async def list(self, context: Context, user: discord.User):
        users = db["users_global"]
        user_data = users.find_one({"id": user.id})

        if user_data is None:
            user_data = CONSTANTS.user_global_data_template(user.id)
            users.insert_one(user_data)

        if not "strikes" in user_data:
            user_data["strikes"] = []

        embed = discord.Embed(
            title=f"Strikes for {user}",
            color=0xBEBEFE
        )

        for i, strike in enumerate(user_data["strikes"]):
            embed.add_field(name=f"Strike at {strike['time']} | ID: {i}", value=strike["reason"], inline=False)

        await context.send(embed=embed)

    @commands.command(
        name="dm",
        description="DM a user",
    )
    @commands.is_owner()
    async def dm(self, context: Context, user: discord.User, *, message: str) -> None:
        try:
            await user.send(message)
            await context.send(f"Sent message to {user.mention}")
        except Exception as e:
            await context.send(f"Could not send message to {user.mention} due to: {e}")

    @commands.command(
        name="simulate-level-up",
        description=""
    )
    @commands.is_owner()
    async def simulate_level_up(self, context: Context):
        author = context.author

        c = db["users"]
        data = await CachedDB.find_one(c, {"id": author.id, "guild_id": context.guild.id})

        guilds = db["guilds"]
        guild_data = await CachedDB.find_one(guilds, {"id": context.guild.id})

        if data:
            channel = context.channel
            if guild_data:
                if "level_announce_channel" in guild_data:
                    if guild_data["level_announce_channel"] != 0:
                        channel = context.guild.get_channel(guild_data["level_announce_channel"])

                if "should_announce_levelup" in guild_data:
                    if guild_data["should_announce_levelup"]:
                        await channel.send(f"{author.mention} leveled up to level {data['level']}!")
                else:
                    await channel.send(f"{author.mention} leveled up to level {data['level']}!")

async def setup(bot) -> None:
    await bot.add_cog(Owner(bot))
