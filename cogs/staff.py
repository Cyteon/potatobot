# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon

from cryptography.fernet import Fernet
import os

import re
from datetime import datetime, timedelta
import aiohttp

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

from utils import DBClient, CONSTANTS, Checks, CachedDB

client = DBClient.client
db = client.potatobot

class Staff(commands.Cog, name="👮‍♂️ Staff"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.prefixDB = bot.prefixDB

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        if message.author == self.bot.user or message.author.bot:
            return

        if message.author.guild_permissions.administrator:
            return

        c = db["guilds"]
        data = await CachedDB.find_one(c, {"id": message.guild.id})

        if not data:
            data = CONSTANTS.guild_data_template(message.guild.id)
            c.insert_one(data)

        if not data["log_channel"]:
            return

        log_channel = message.guild.get_channel(data["log_channel"])

        if not log_channel:
            return

        embed = discord.Embed(
            title="Message Deleted",
            description=f"Message sent by {message.author.mention} deleted in {message.channel.mention}",
            color=discord.Color.red()
        )

        embed.add_field(
            name="Content",
            value=message.content
        )

        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        if before.author == self.bot.user or before.author.bot:
            return

        if before.author.guild_permissions.administrator:
            return

        if before.content == after.content:
            return

        c = db["guilds"]
        data = await CachedDB.find_one(c, {"id": before.guild.id})

        if not data:
            data = CONSTANTS.guild_data_template(before.guild.id)
            c.insert_one(data)

        if not data["log_channel"]:
            return

        log_channel = before.guild.get_channel(data["log_channel"])

        if not log_channel:
            return

        embed = discord.Embed(
            title="Message Edited",
            description=f"Message sent by {before.author.mention} edited in {before.channel.mention}",
            color=discord.Color.orange()
        )

        embed.add_field(
            name="Before",
            value=before.content
        )

        embed.add_field(
            name="After",
            value=after.content
        )

        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, user: discord.User) -> None:
        c = db["guilds"]
        guild = user.guild

        data = await CachedDB.find_one(c, {"id": guild.id})

        if not data:
            data = CONSTANTS.guild_data_template(guild.id)
            c.insert_one(data)

        if not data["log_channel"]:
            return

        log_channel = guild.get_channel(data["log_channel"])

        if not log_channel:
            return

        embed = discord.Embed(
            title="Member Left",
            description=f"{user.mention} left the server",
            color=discord.Color.red()
        )

        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User) -> None:
        c = db["guilds"]

        data = await CachedDB.find_one(c, {"id": guild.id})

        if not data:
            data = CONSTANTS.guild_data_template(guild.id)
            c.insert_one(data)

        if not data["log_channel"]:
            return

        log_channel = guild.get_channel(data["log_channel"])

        if not log_channel:
            return

        embed = discord.Embed(
            title="Member Banned",
            description=f"{user.mention} was banned",
            color=discord.Color.red()
        )

        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User) -> None:
        c = db["guilds"]

        data = await CachedDB.find_one(c, {"id": guild.id})

        if not data:
            data = CONSTANTS.guild_data_template(guild.id)
            c.insert_one(data)

        if not data["log_channel"]:
            return

        log_channel = guild.get_channel(data["log_channel"])

        if not log_channel:
            return

        embed = discord.Embed(
            title="Member Unbanned",
            description=f"{user.mention} was unbanned",
            color=discord.Color.green()
        )

        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_kick(self, guild: discord.Guild, user: discord.User) -> None:
        c = db["guilds"]

        data = await CachedDB.find_one(c, {"id": guild.id})

        if not data:
            data = CONSTANTS.guild_data_template(guild.id)
            c.insert_one(data)

        if not data["log_channel"]:
            return

        log_channel = guild.get_channel(data["log_channel"])

        if not log_channel:
            return

        embed = discord.Embed(
            title="Member Kicked",
            description=f"{user.mention} was kicked",
            color=discord.Color.red()
        )

        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, user: discord.User) -> None:
        if user.bot:
            return

        users = db["users"]
        user_data = await CachedDB.find_one(users, {"id": user.id})

        guilds = db["guilds"]

        data = await CachedDB.find_one(guilds, {"id": user.guild.id})


        if not data:
            data = CONSTANTS.guild_data_template(user.guild.id)
            guilds.insert_one(data)

        if user_data:
            if "jailed" in user_data:
                if user_data["jailed"]:
                    if "jail_role" in data:
                        role = None
                        jail_channel = None

                        if data["jail_role"] == 0:
                            role = await user.guild.create_role(name="Jailed", reason="Jail role created by PotatoBot")
                            data["jail_role"] = role.id

                            newdata = {"$set": {"jail_role": role.id}}
                            guilds.update_one({"id": user.guild.id}, newdata)
                        else:
                            role = user.guild.get_role(data["jail_role"])

                        for old_role in user.roles:
                            if old_role == user.guild.default_role:
                                continue

                            await user.remove_roles(old_role)

                        await user.add_roles(role, reason="User is jailed and tried to rejoin")

                        return

        if not "default_role" in data:
            return

        default_role = user.guild.get_role(data["default_role"])

        if default_role:
            await user.add_roles(default_role)


    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages) -> None:
        embed = discord.Embed(
            title="Bulk Message Delete",
            description=f"{len(messages)} messages were deleted",
            color=discord.Color.red()
        )

        c = db["guilds"]
        #data = c.find_one({"id": messages[0].guild.id})
        data = await CachedDB.find_one(c, {"id": messages[0].guild.id})

        if not data:
            data = CONSTANTS.guild_data_template(messages[0].guild.id)
            c.insert_one(data)

        if not data["log_channel"]:
            return

        log_channel = messages[0].guild.get_channel(data["log_channel"])

        if not log_channel:
            return

        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.TextChannel):
        embed = discord.Embed(
            title = "Channel Created",
            description = f"Channel {channel.mention} was created",
            color = discord.Color.green()
        )

        c = db["guilds"]
        data = c.find_one({"id": channel.guild.id})

        if not data:
            data = CONSTANTS.guild_data_template(channel.guild.id)
            c.insert_one(data)

        if not data["log_channel"]:
            return

        log_channel = channel.guild.get_channel(data["log_channel"])

        if not log_channel:
            return

        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.TextChannel):
        embed = discord.Embed(
            title = "Channel Deleted",
            description = f"Channel {channel.mention} ({channel.name}) was deleted",
            color = discord.Color.red()
        )

        c = db["guilds"]
        data = c.find_one({"id": channel.guild.id})

        if not data:
            data = CONSTANTS.guild_data_template(channel.guild.id)
            c.insert_one(data)

        if not data["log_channel"]:
            return

        log_channel = channel.guild.get_channel(data["log_channel"])

        if not log_channel:
            return

        try:
            await log_channel.send(embed=embed)
        except:
            pass

    @commands.command(
        name="prefix",
        description="Change the bot prefix",
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_channels=True)
    async def prefix(self, context: commands.Context, prefix: str = "none"):
        if prefix == "none":
            return await context.send("Current prefix is: `" + self.prefixDB.get(str(context.guild.id)) + "`")

        if prefix == "/":
            return await context.send("Prefix cannot be `/`")

        guild_id = str(context.guild.id)
        self.prefixDB.set(guild_id, prefix)
        self.prefixDB.dump()
        await context.send(f"Prefix set to {prefix}")

    @commands.hybrid_command(
        name="groq-api-key",
        description="Set API key for AI"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_channels=True)
    async def groq_api_key(self, context: commands.Context, key: str):
        c = db["guilds"]
        data = c.find_one({"id": context.guild.id})

        if not data:
            data = CONSTANTS.guild_data_template(context.guild.id)
            c.insert_one(data)

        cipher_suite = Fernet(os.getenv("HASHING_SECRET"))
        cipher_text = cipher_suite.encrypt(key.encode())

        await context.send(key)

        try:
            await context.message.delete()
        except:
            pass

        newdata = { "$set": { "groq_api_key": cipher_text } }

        c.update_one({"id": context.guild.id}, newdata)

        await context.send(f"Set groq api key")

    @commands.hybrid_group(
        name="settings",
        description="Command to change server settings",
        aliases=["setting"],
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_channels=True)
    async def settings(self, context: Context) -> None:
        subcommands = [cmd for cmd in self.settings.walk_commands()]

        data = []

        for subcommand in subcommands:
            description = subcommand.description.partition("\n")[0]
            data.append(f"{await self.bot.get_prefix(context)}settings {subcommand.name} - {description}")

        help_text = "\n".join(data)
        embed = discord.Embed(
            title=f"Help: Settings", description="List of available commands:", color=0xBEBEFE
        )
        embed.add_field(
            name="Commands", value=f"```{help_text}```", inline=False
        )

        await context.send(embed=embed)

    @settings.command(
        name="show",
        description="Show server settings"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_channels=True)
    async def show(self, context: Context) -> None:
        c = db["guilds"]
        data = c.find_one({"id": context.guild.id})

        if not data:
            data = CONSTANTS.guild_data_template(context.guild.id)
            c.insert_one(data)

        embed = discord.Embed(
            title="Server Settings",
            color=discord.Color.blue()
        )

        #for s in subcommands:
            #embed.add_field(
                #name=s,
                #value=str(data[s])
            #)

        embed.add_field( name="Daily Cash", value=data["daily_cash"] )
        embed.add_field( name="Tickets Category",
                        value=context.guild.get_channel(data["tickets_category"]).name.capitalize() if data["tickets_category"] else "None" )
        embed.add_field( name="Tickets Support Role",
                        value=context.guild.get_role(data["tickets_support_role"]).mention if data["tickets_support_role"] else "None" )
        embed.add_field( name="Log Channel", value=context.guild.get_channel(data["log_channel"]).mention if data["log_channel"] else "None" )
        embed.add_field( name="Level Roles", value="`/setting level_roles show`")
        embed.add_field( name="Level Announce Channel",
                        value=context.guild.get_channel( data["level_announce_channel"]).mention if (
                                "level_announce_channel" in data and context.guild.get_channel(data["level_announce_channel"]) != None
                            ) else "None"
                        )
        embed.add_field( name="Should announce levelup", value=data["should_announce_levelup"] if "should_announce_levelup" in data else "idk")

        await context.send(embed=embed)

    @settings.command(
        name="should-announce-levelup",
        description="Should announce levelup"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_roles=True)
    async def should_announce_levelup(self, context: Context, enabled: bool) -> None:
        c = db["guilds"]
        data = c.find_one({"id": context.guild.id})

        if not data:
            data = CONSTANTS.guild_data_template(context.guild.id)
            c.insert_one(data)

        newdata = { "$set": { "should_announce_levelup": enabled } }

        c.update_one({"id": context.guild.id}, newdata)

        await context.send(f"Set should announce levelup to {enabled}")

    @settings.command(
        name="daily-cash",
        description="Set daily cash amount"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(administrator=True)
    async def daily_cash(self, context: Context, amount: int) -> None:
        c = db["guilds"]

        data = c.find_one({"id": context.guild.id})

        if not data:
            data = CONSTANTS.guild_data_template(context.guild.id)
            c.insert_one(data)

        newdata = { "$set": { "daily_cash": amount } }

        c.update_one({"id": context.guild.id}, newdata)

        await context.send(f"Set daily cash to {amount}")



    @settings.command(
        name="tickets-category",
        description="Set category where tickets are created"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(administrator=True)
    async def tickets_category(self, context: Context, category: discord.CategoryChannel) -> None:
        c = db["guilds"]

        data = c.find_one({"id": context.guild.id})

        if not data:
            data = CONSTANTS.guild_data_template(context.guild.id)
            c.insert_one(data)

        newdata = { "$set": { "tickets_category": category.id } }

        c.update_one({"id": context.guild.id}, newdata)

        await context.send(f"Set tickets category to {category.mention}")

    @settings.command(
        name="level-up-channel",
        description="Set level up announce channel"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_channels=True)
    async def level_up_channel(self, context: Context, channel: discord.TextChannel) -> None:
        c = db["guilds"]

        data = c.find_one({"id": context.guild.id})

        if not data:
            data = CONSTANTS.guild_data_template(context.guild.id)
            c.insert_one(data)

        newdata = { "$set": { "level_announce_channel": channel.id } }

        c.update_one({"id": context.guild.id}, newdata)

        await context.send(f"Set level announce channel to {channel.mention}")

    @settings.command(
        name="tickets-support-role",
        description="Set ticket support role"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_roles=True)
    async def tickets_support_role(self, context: Context, role: discord.Role) -> None:
        c = db["guilds"]

        data = c.find_one({"id": context.guild.id})

        if not data:
            data = CONSTANTS.guild_data_template(context.guild.id)
            c.insert_one(data)

        newdata = { "$set": { "tickets_support_role": role.id } }

        c.update_one({"id": context.guild.id}, newdata)

        await context.send(f"Set tickets support role to {role.mention}")

    @settings.command(
        name="log-channel",
        description="Set log channel"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_channels=True)
    async def log_channel(self, context: Context, channel: discord.TextChannel) -> None:
        c = db["guilds"]

        data = c.find_one({"id": context.guild.id})

        if not data:
            data = CONSTANTS.guild_data_template(context.guild.id)
            c.insert_one(data)

        newdata = { "$set": { "log_channel": channel.id } }

        c.update_one({"id": context.guild.id}, newdata)

        await context.send(f"Set log channel to {channel.mention}")

    @settings.command(
        name="default-role",
        description="Set default role to be given to new members"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_roles=True)
    async def default_role(self, context: Context, role: discord.Role) -> None:
        c = db["guilds"]

        data = c.find_one({"id": context.guild.id})

        if not data:
            data = CONSTANTS.guild_data_template(context.guild.id)
            c.insert_one(data)

        dangerous_permissions = [
            "administrator",
            "manage_guild",
            "manage_roles",
            "manage_channels",
            "manage_messages",
            "kick_members",
            "ban_members",
            "manage_webhooks",
            "manage_emojis",
            "manage_nicknames",
        ]

        for permission in dangerous_permissions:
            if getattr(role.permissions, permission):
                return await context.send("The role has dangerous permissions. Please choose a role without dangerous permissions.")

        newdata = { "$set": { "default_role": role.id } }

        c.update_one({"id": context.guild.id}, newdata)

        await context.send(f"Set default role to {role.name}")

    @settings.group(
        name="level-roles",
        description="Commands to set up level roles",
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_roles=True)
    async def level_roles(self, context: Context) -> None:
        c = db["guilds"]
        data = c.find_one({"id": context.guild.id})

        if not data:
            data = CONSTANTS.guild_data_template(context.guild.id)
            c.insert_one(data)

        embed = discord.Embed(
            title="Level Roles",
            color=discord.Color.blue()
        )


        for r in data["level_roles"]:
            embed.add_field(
                name=r,
                value=context.guild.get_role(data["level_roles"][r]).mention
            )

        await context.send(embed=embed)

    @level_roles.command(
        name="show",
        description="Show level roles"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_roles=True)
    async def show_level_roles(self, context: Context) -> None:
        c = db["guilds"]
        data = c.find_one({"id": context.guild.id})

        if not data:
            data = CONSTANTS.guild_data_template(context.guild.id)
            c.insert_one(data)

        embed = discord.Embed(
            title="Level Roles",
            color=discord.Color.blue()
        )

        for r in data["level_roles"]:
            embed.add_field(
                name=r,
                value=context.guild.get_role(data["level_roles"][r]).mention
            )

        await context.send(embed=embed)


    @level_roles.command(
        name="set",
        description="Set level roles"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_roles=True)
    async def set(self, context: Context, level: int, role: discord.Role) -> None:
        c = db["guilds"]
        data = c.find_one({"id": context.guild.id})

        if not data:
            data = CONSTANTS.guild_data_template(context.guild.id)
            c.insert_one(data)

        level_roles = data["level_roles"]
        level_roles[str(level)] = role.id

        newdata = { "$set": { "level_roles": level_roles } }
        c.update_one({"id": context.guild.id}, newdata)

        await context.send(f"Set level {level} role to {role.mention}")

    @commands.hybrid_command(
        name="kick",
        description="Kick a user out of the server.",
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    @app_commands.describe(
        user="The user that should be kicked.",
        reason="The reason why the user should be kicked.",
    )
    async def kick(
        self, context: Context, user: discord.User, *, reason: str = "Not specified"
    ) -> None:
        member = context.guild.get_member(user.id) or await context.guild.fetch_member(
            user.id
        )

        if member == self.bot.user:
            return await context.send("what did i do :C")

        if member.guild_permissions.administrator:
            embed = discord.Embed(
                description="User has administrator permissions.", color=0xE02B2B
            )
            await context.send(embed=embed)
        else:
            try:
                messaged = False

                try:
                    await member.send(f"You were kicked by **{context.author}** from **{context.guild.name}**!\nReason: {reason}")
                    messaged = True
                except:
                    # Couldn't send a message in the private messages of the user
                    pass
                await member.kick(reason=reason)

                embed = discord.Embed(
                    description=f"**{member}** was kicked by **{context.author}**!",
                    color=0xBEBEFE,
                )
                embed.add_field(name="Reason:", value=reason)
                embed.add_field(name="Messaged User:", value="Yes" if messaged else "No")
                await context.send(embed=embed)

                guilds = db["guilds"]
                data = guilds.find_one({"id": context.guild.id})

                if not data:
                    data = CONSTANTS.guild_data_template(context.guild.id)
                    guilds.insert_one(data)

                if "log_channel" in data:
                    log_channel = context.guild.get_channel(data["log_channel"])

                    if log_channel:
                        embed = discord.Embed(
                            title="Member Kicked",
                            description=f"{member.mention} was kicked by {context.author.mention}",
                            color=discord.Color.red()
                        )

                        embed.add_field(
                            name="Reason",
                            value=reason
                        )

                        await log_channel.send(embed=embed)

            except:
                embed = discord.Embed(
                    description="An error occurred while trying to kick the user. Make sure my role is above the role of the user you want to kick.",
                    color=0xE02B2B,
                )
                await context.send(embed=embed)

    @commands.hybrid_command(
        name="nick",
        aliases=["n"],
        description="Change the nickname of a user on a server.",
        usage="nick <user> <nickname>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def nick(
        self, context: Context, user: discord.User, *, nickname: str = None
    ) -> None:
        member = context.guild.get_member(user.id) or await context.guild.fetch_member(
            user.id
        )
        try:
            await member.edit(nick=nickname)
            embed = discord.Embed(
                description=f"**{member}'s** new nickname is **{nickname}**!",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
        except:
            embed = discord.Embed(
                description="An error occurred while trying to change the nickname of the user. Make sure my role is above the role of the user you want to change the nickname.",
                color=0xE02B2B,
            )
            await context.send(embed=embed)

    @commands.hybrid_command(
        name="ban",
        description="Bans a user from the server.",
        usage="ban <user> [reason]"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(
        self, context: Context, user: discord.User, *, reason: str = "Not specified"
    ) -> None:
        member = context.guild.get_member(user.id) or await context.guild.fetch_member(
            user.id
        )

        if member == self.bot.user:
            return await context.send("what did i do :C")

        try:
            if member.guild_permissions.administrator:
                embed = discord.Embed(
                    description="User has administrator permissions.", color=0xE02B2B
                )
                await context.send(embed=embed)
            else:
                messaged = False
                try:
                    await member.send(
                        f"You were banned by **{context.author}** from **{context.guild.name}**!\nReason: {reason}"
                    )
                    messaged = True
                except:
                    # Couldn't send a message in the private messages of the user
                    pass

                await member.ban(reason=reason, delete_message_days=0)

                embed = discord.Embed(
                    description=f"**{member}** was banned by **{context.author}**!",
                    color=0xBEBEFE,
                )
                embed.add_field(name="Reason:", value=reason)
                embed.add_field(name="Messaged User:", value="Yes" if messaged else "No")
                await context.send(embed=embed)

                guilds = db["guilds"]
                data = guilds.find_one({"id": context.guild.id})

                if not data:
                    data = CONSTANTS.guild_data_template(context.guild.id)
                    guilds.insert_one(data)

                if "log_channel" in data:
                    log_channel = context.guild.get_channel(data["log_channel"])

                    if log_channel:
                        embed = discord.Embed(
                            title="Member Banned",
                            description=f"{member.mention} was banned by {context.author.mention}",
                            color=discord.Color.red()
                        )

                        embed.add_field(
                            name="Reason",
                            value=reason
                        )

                        await log_channel.send(embed=embed)
        except:
            embed = discord.Embed(
                title="Error!",
                description="An error occurred while trying to ban the user. Make sure my role is above the role of the user you want to ban.",
                color=0xE02B2B,
            )
            await context.send(embed=embed)

    @commands.hybrid_command(
        name="hackban",
        description="Ban a user that is not in the server",
        usage="hackban <user> [reason]",
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def hackban(self, context: Context, user: discord.User, reason: str = "Not specified"):
        if user == self.bot.user:
            return await context.send("what did i do :C")

        try:
            await context.guild.ban(user, reason=reason, delete_message_days=0)

            embed = discord.Embed(
                title="User Hackbanned",
                description=f"**{user}** was hackbanned by **{context.author}**!",
                color=0xBEBEFE,
            )

            embed.add_field(name="Reason:", value=reason)

            guilds = db["guilds"]
            data = guilds.find_one({"id": context.guild.id})

            if not data:
                data = CONSTANTS.guild_data_template(context.guild.id)
                guilds.insert_one(data)

            if "log_channel" in data:
                log_channel = context.guild.get_channel(data["log_channel"])

                if log_channel:
                    await log_channel.send(embed=embed)

            await context.send(f"Banned **{user}**!")
        except:
            embed = discord.Embed(
                title="Error!",
                description="An error occurred while trying to ban the user.",
                color=0xE02B2B,
            )

            await context.send(embed=embed)

    @commands.hybrid_command(
        name="softban",
        description="Bans and unbans a user from the server to delete messages",
        usage="softban <user>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def softban(self, context: Context, user: discord.User):
        if user == self.bot.user:
            return await context.send("what did i do :C")

        try:
            user = context.guild.get_member(user.id) or await context.guild.fetch_member(
                user.id
            )

            if user.guild_permissions.administrator:
                embed = discord.Embed(
                    description="User has administrator permissions.", color=0xE02B2B
                )
                return await context.send(embed=embed)

            await context.guild.ban(user, reason="Softban", delete_message_days=7)
            await context.guild.unban(user, reason="Softban")
            embed = discord.Embed(
                description=f"**{user}** was softbanned by **{context.author}**!",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                description="An error occurred while trying to softban the user, " + str(e),
                color=0xE02B2B,
            )
            await context.send(embed=embed)


    @commands.hybrid_command(
        name="unban",
        description="Unban a user from the server.",
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, context: Context, user: discord.User):
        try:
            banned_users = context.guild.bans()
            async for ban_entry in banned_users:
                if ban_entry.user.id == user.id:
                    await context.guild.unban(user)
                    embed = discord.Embed(
                        description=f"**{user}** was unbanned by **{context.author}**!",
                        color=0xBEBEFE,
                    )
                    await context.send(embed=embed)

                    try:
                        await user.send(
                            f"You were unbanned by **{context.author}** from **{context.guild.name}**!"
                        )
                    except:
                        # Couldn't send a message in the private messages of the user
                        pass

                    guilds = db["guilds"]
                    guild = guilds.find_one({"id": context.guild.id})

                    if not guild:
                        guild = CONSTANTS.guild_data_template(context.guild.id)
                        guilds.insert_one(guild)

                    if "log_channel" in guild:
                        log_channel = context.guild.get_channel(guild["log_channel"])

                        if log_channel:
                            embed = discord.Embed(
                                title="Member Unbanned",
                                description=f"{user.mention} was unbanned by {context.author.mention}",
                                color=discord.Color.green()
                            )

                            await log_channel.send(embed=embed)

                    return
            embed = discord.Embed(
                description="User is not banned.", color=0xE02B2B
            )
            await context.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                description="An error occurred while trying to unban the user: " + str(e),
                color=0xE02B2B,
            )
            await context.send(embed=embed)

    @commands.hybrid_command(
        name="purge",
        description="Delete a number of messages.",
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_guild_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @app_commands.describe(amount="The amount of messages that should be deleted.")
    async def purge(self, context: Context, amount: int) -> None:


        await context.send(
            "Deleting messages..."
        )  # Bit of a hacky way to make sure the bot responds to the interaction and doens't get a "Unknown Interaction" response
        purged_messages = await context.channel.purge(limit=amount + 1)
        embed = discord.Embed(
            description=f"**{context.author}** cleared **{len(purged_messages)-1}** messages!",
            color=0xBEBEFE,
        )
        await context.channel.send(embed=embed)


    @commands.hybrid_command(
        name="archive",
        description="Archives in a text file the last messages with a chosen limit of messages.",
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_messages=True)
    async def archive(self, context: Context, limit: int = 10) -> None:
        os.makedirs("logs", exist_ok=True)
        log_file = f"logs/{context.channel.id}.log"
        with open(log_file, "w", encoding="UTF-8") as f:
            f.write(
                f'Archived messages from: #{context.channel} ({context.channel.id}) in the guild "{context.guild}" ({context.guild.id}) at {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}\n'
            )
            async for message in context.channel.history(
                limit=limit, before=context.message
            ):
                attachments = []
                for attachment in message.attachments:
                    attachments.append(attachment.url)
                attachments_text = (
                    f"[Attached File{'s' if len(attachments) >= 2 else ''}: {', '.join(attachments)}]"
                    if len(attachments) >= 1
                    else ""
                )
                f.write(
                    f"{message.created_at.strftime('%d.%m.%Y %H:%M:%S')} {message.author} {message.id}: {message.clean_content} {attachments_text}\n"
                )
        f = discord.File(log_file)
        await context.send(file=f)
        os.remove(log_file)

    @commands.hybrid_command(
        name="mute",
        aliases=["timeout"],
        description="Mute a user in the server."
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def mute(self, context: Context, user: discord.Member, time: str, *, reason: str = "Not specified") -> None:
        if user == self.bot.user:
            return await context.send("what did i do :C")

        try:
            # Try to parse the string as a datetime
            dt = datetime.fromisoformat(time)
            return dt
        except ValueError:
            pass

        # If the string is not a valid datetime, try to parse it as a duration
        pattern = r'^(\d+)([ydhmsw])$'
        match = re.match(pattern, time)

        if not match:
            return await context.send(f"Invalid duration string: {time}")

        value, unit = int(match.group(1)), match.group(2)
        duration = {
            'y': timedelta(days=365*value),
            'w': timedelta(days=7*value),
            'month': timedelta(days=30*value),
            'd': timedelta(days=value),
            'h': timedelta(hours=value),
            'm': timedelta(minutes=value),
            's': timedelta(seconds=value),
        }

        delta = duration[unit]

        await user.timeout(delta, reason=reason)
        await context.send(f"{user.mention} has been muted for {delta}")

        try:
            await user.send(f"You have been muted in {context.guild.name} for {delta} for the following reason: {reason}")
        except:
            pass

    @commands.hybrid_command(
        name="unmute",
        aliases=["untimeout"],
        description="Unmute a user in the server."
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def unmute(self, context: Context, user: discord.Member, *, reason: str = "Not specified") -> None:
        await user.timeout(None, reason=reason)
        await context.send(f"{user.mention} has been unmuted")

        try:
            await user.send(f"You have been unmuted in {context.guild.name} for the following reason: {reason}")
        except:
            pass

    @commands.hybrid_command(
        name="lock",
        description="Lock a channel."
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def lockdown(self, context: Context, channel: discord.TextChannel = None) -> None:
        if not channel:
            channel = context.channel

        overwrite = discord.PermissionOverwrite()
        overwrite = channel.overwrites_for(context.guild.default_role)
        overwrite.send_messages = False

        await channel.set_permissions(context.guild.default_role, overwrite=overwrite)

        await context.send(f"{channel.mention} has been locked down")

        await channel.send(f"# 🔒 This channel has been locked by staff")

    @commands.hybrid_command(
        name="unlock",
        description="Unlock a channel."
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def unlock(self, context: Context, channel: discord.TextChannel = None) -> None:
        if not channel:
            channel = context.channel

        overwrite = discord.PermissionOverwrite()
        overwrite = channel.overwrites_for(context.guild.default_role)
        overwrite.send_messages = None

        await channel.set_permissions(context.guild.default_role, overwrite=overwrite)

        await context.send(f"{channel.mention} has been unlocked")

        await channel.send(f"# 🔓 This channel has been unlocked by staff")

    @commands.hybrid_command(
        name="stealemoji",
        description="Steal an emoji from another server."
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_emojis=True)
    @commands.bot_has_permissions(manage_emojis=True)
    async def stealemoji(self, context: Context, emoji: discord.PartialEmoji, name: str) -> None:
        try:
            emoji_bytes = await emoji.read()
            await context.guild.create_custom_emoji(
                name=name if name else emoji.name,
                image=emoji_bytes,
                reason=f"Emoji yoinked by {context.author} VIA {context.guild.me.name}",
            )
            await context.send(
                embed=discord.Embed(
                    description=f"Emoji Stolen",
                    color=discord.Color.random(),
                ).set_image(url=emoji.url)
            )
        except Exception as e:
            await context.send(str(e))

    @commands.hybrid_command(
        name="emojifromurl",
        description="Add an emoji from a URL."
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_emojis=True)
    @commands.bot_has_permissions(manage_emojis=True)
    async def emojifromurl(self, context: Context, url: str, name: str) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    emoji_bytes = await response.read()
                    await context.guild.create_custom_emoji(
                        name=name,
                        image=emoji_bytes,
                        reason=f"Emoji added by {context.author} VIA {context.guild.me.name}",
                    )
                    await context.send(
                        embed=discord.Embed(
                            description=f"Emoji added",
                            color=discord.Color.random(),
                        ).set_image(url=url)
                    )
                else:
                    await context.send("Failed to download the emoji")

    @commands.hybrid_command(
        name="jail",
        description="Jail a user."
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_roles=True, manage_channels=True, manage_messages=True)
    @commands.bot_has_permissions(manage_roles=True, manage_channels=True, manage_messages=True)
    async def jail(self, context: Context, user: discord.Member, *, reason: str = "Not specified") -> None:
        await context.send("Jailing user... please wait")
        guilds = db["guilds"]
        data = await CachedDB.find_one(guilds, {"id": context.guild.id})

        if not data:
            data = CONSTANTS.guild_data_template(context.guild.id)
            guilds.insert_one(data)

        role = None
        jail_channel = None

        if "jail_role" in data:
            if data["jail_role"] == 0:
                role = await context.guild.create_role(name="Jailed", reason="Jail role created by PotatoBot")
                data["jail_role"] = role.id

                newdata = {"$set": {"jail_role": role.id}}
                guilds.update_one({"id": context.guild.id}, newdata)
            else:
                role = context.guild.get_role(data["jail_role"])
        else:
            role = await context.guild.create_role(name="Jailed", reason="Jail role created by PotatoBot")
            data["jail_role"] = role.id

            newdata = {"$set": {"jail_role": role.id}}
            guilds.update_one({"id": context.guild.id}, newdata)


        if "jail_channel" in data:
            if data["jail_channel"] == 0:
                jail_channel = await context.guild.create_text_channel(name="jail", reason="Jail channel created by PotatoBot")
                data["jail_channel"] = jail_channel.id

                newdata = {"$set": {"jail_channel": jail_channel.id}}
                guilds.update_one({"id": context.guild.id}, newdata)
            else:
                jail_channel = context.guild.get_channel(data["jail_channel"])
        else:
            jail_channel = await context.guild.create_text_channel(name="jail", reason="Jail channel created by PotatoBot")
            data["jail_channel"] = jail_channel.id

            newdata = {"$set": {"jail_channel": jail_channel.id}}
            guilds.update_one({"id": context.guild.id}, newdata)

        for old_role in user.roles:
            if old_role == context.guild.default_role:
                continue

            await user.remove_roles(old_role)

        await user.add_roles(role, reason=reason)

        for channel in context.guild.channels:
            if channel == jail_channel:
                continue

            await channel.set_permissions(role, view_channel=False)

        if not jail_channel:
            jail_channel = await context.guild.create_text_channel(name="jail", reason="Jail channel created by PotatoBot")
            data["jail_channel"] = jail_channel.id

            newdata = {"$set": {"jail_channel": jail_channel.id}}
            guilds.update_one({"id": context.guild.id}, newdata)

        await jail_channel.set_permissions(context.guild.default_role, view_channel=False)
        await jail_channel.set_permissions(role, view_channel=True)

        users = db["users"]
        user_data = await CachedDB.find_one(users, {"id": user.id})

        if not user_data:
            user_data = CONSTANTS.user_data_template(context.guild.id, user.id)
            users.insert_one(user_data)

        newdata = {
            "$set": { "jailed": True }
        }

        await CachedDB.update_one(users, {"id": user.id}, newdata)

        await context.send(f"{user.mention} has been jailed")

        embed = discord.Embed(
            description = "You have been jailed for reason: **" + reason + "**",
            color = 0xBEBEFE
        )
        await jail_channel.send(user.mention, embed=embed)

    @commands.hybrid_command(
        name="unjail",
        description="Unjail a user."
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_roles=True, manage_channels=True, manage_messages=True)
    @commands.bot_has_permissions(manage_roles=True, manage_channels=True, manage_messages=True)
    async def unjail(self, context: Context, user: discord.Member):
        guilds = db["guilds"]
        data = guilds.find_one({"id": context.guild.id})

        await user.remove_roles(context.guild.get_role(data["jail_role"]))

        users = db["users"]
        user_data = await CachedDB.find_one(users, {"id": user.id})

        if not user_data:
            user_data = CONSTANTS.user_data_template(context.guild.id, user.id)
            users.insert_one(user_data)

        newdata = {
            "$set": { "jailed": False }
        }

        await CachedDB.update_one(users, {"id": user.id}, newdata)

        await context.send(f"{user.mention} has been unjailed")

    @commands.hybrid_group(
        name="warnings",
        description="Commands to warn users",
        usage="warnings"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def warnings(self, context: Context) -> None:
        subcommands = [cmd for cmd in self.warnings.walk_commands()]

        data = []

        for subcommand in subcommands:
            description = subcommand.description.partition("\n")[0]
            data.append(f"{await self.bot.get_prefix(context)}warnings {subcommand.name} - {description}")

        help_text = "\n".join(data)
        embed = discord.Embed(
            title=f"Help: Warnings", description="List of available commands:", color=0xBEBEFE
        )
        embed.add_field(
            name="Commands", value=f"```{help_text}```", inline=False
        )

        await context.send(embed=embed)

    @warnings.command(
        name="add",
        description="Warn a user."
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_messages=True)
    async def warn(self, context: Context, user: discord.Member, *, reason: str = "Not specified") -> None:
        users = db["users"]
        data = users.find_one({"id": user.id, "guild_id": context.guild.id})

        if not data:
            data = CONSTANTS.user_data_template(user.id, context.guild.id)
            users.insert_one(data)

        if not "warnings" in data:
            data["warnings"] = []

        data["warnings"].append({"reason": reason, "time": datetime.now().strftime("%d.%m.%Y %H:%M:%S")})

        newdata = {"$set": {"warnings": data["warnings"]}}

        users.update_one({"id": user.id, "guild_id": context.guild.id}, newdata)

        await context.send(f"{user.mention} has been warned for {reason}")

    @warnings.command(
        name="list",
        description="Get a user's warnings."
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_messages=True)
    async def listwarnings(self, context: Context, user: discord.Member) -> None:
        users = db["users"]
        data = users.find_one({"id": user.id, "guild_id": context.guild.id})

        if not data:
            data = CONSTANTS.user_data_template(user.id, context.guild.id)
            users.insert_one(data)


        embed = discord.Embed(
            title=f"Warnings for {user}",
            color=discord.Color.red()
        )

        for w in data["warnings"]:
            embed.add_field(
                name=w["time"],
                value=w["reason"],
                inline=False
            )

        await context.send(embed=embed)

    @warnings.command(
        name="clear",
        description="Clear a user's warnings."
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_messages=True)
    async def clearwarnings(self, context: Context, user: discord.Member) -> None:
        users = db["users"]
        data = users.find_one({"id": user.id, "guild_id": context.guild.id})

        if not data:
            data = CONSTANTS.user_data_template(user.id, context.guild.id)
            users.insert_one(data)

        newdata = {"$set": {"warnings": []}}

        users.update_one({"id": user.id, "guild_id": context.guild.id}, newdata)

        await context.send(f"Cleared warnings for {user.mention}")

    @commands.hybrid_command(
        name="recreate",
        description="Recreates channel with same settings",
        usage="recreate"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def recreate(self, context: Context) -> None:
        await context.send("Are you sure you want to recreate this channel?", view=deleteconfirm(context.author, context.channel))

class deleteconfirm(discord.ui.View):
    def __init__(self, user, channel):
        super().__init__(timeout=None)
        self.user = user
        self.channel = channel

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.red)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            return

        old_channel = self.channel

        await self.channel.delete()

        new_channel = await old_channel.clone()

        await new_channel.edit(position=old_channel.position)

        await new_channel.send("Channel has been recreated")

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.green)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()

async def setup(bot) -> None:
    await bot.add_cog(Staff(bot))
