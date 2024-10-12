# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon


import discord
import asyncio
import datetime
import logging
import os

logger = logging.getLogger("discord_bot")

from discord.ext import commands, tasks
from discord.ext.commands import Context
from utils import CONSTANTS, DBClient, Checks, CachedDB

KICK_TRESHOLD = 5
BAN_TRESHOLD = 3
DELETE_TRESHOLD = 2
PING_TRESHOLD = 12
WEBHOOK_TRESHOLD = 40

client = DBClient.client
db = client.potatobot

ban_cache = {}
kick_cache = {}
ping_cache = {}
webhook_cache = {}
delete_cache = {}

deleted_channels = {}

class Security(commands.Cog, name="🛡️ Security"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.clear_cache.start()

    @tasks.loop(minutes=10)
    async def clear_cache(self) -> None:
        ban_cache.clear()
        kick_cache.clear()
        ping_cache.clear()
        webhook_cache.clear()
        delete_cache.clear()

        deleted_channels.clear()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.guild == None:
            return

        if message.author == self.bot.user:
            return

        if message.author == message.guild.owner:
            return

        if message.webhook_id:
            try:
                webhook = await self.bot.fetch_webhook(message.webhook_id)
            except discord.NotFound:
                webhook = None

            if not webhook:
                return

            if message.webhook_id in webhook_cache:
                webhook_cache[message.webhook_id] += 1

                if "@everyone" in message.content.lower() or "@here" in message.content.lower():
                    webhook_cache[message.webhook_id] += 11

                if webhook_cache[message.webhook_id] > WEBHOOK_TRESHOLD:
                    guilds = db["guilds"]
                    data = guilds.find_one({"id": message.guild.id})

                    if not data:
                        data = CONSTANTS.guild_data_template(message.guild.id)
                        guilds.insert_one(data)

                    if not "security" in data:
                        return

                    if "anti_webhook_spam" not in data["security"]["antinuke"]:
                        return

                    if not data["security"]["antinuke"]["anti_webhook_spam"]:
                        return

                    await message.delete()


                    log_channel = message.guild.get_channel(data["log_channel"])

                    try:
                        await webhook.delete()

                        embed = discord.Embed(
                            title="AntiSpam Warning",
                            description=f"Webhook **{message.webhook_id}** has been deleted for spamming",
                            color=discord.Color.green()
                        )

                        if log_channel != None:
                            await log_channel.send(embed=embed)
                    except:
                        embed = discord.Embed(
                            title="AntiSpam Warning",
                            description=f"Unable to delete webhook **{message.webhook_id}** for spamming, please delete it manually",
                            color=discord.Color.red()
                        )

                        if log_channel != None:
                            await log_channel.send(embed=embed)


                    embed = discord.Embed(
                        title="AntiSpam Warning",
                        description=f"Webhook **{message.webhook_id}** has triggered the antispam system, last message: `{message.content}`",
                        color=discord.Color.orange()
                    )

                    if log_channel != None:
                        await log_channel.send(embed=embed)
            else:
                webhook_cache[message.webhook_id] = 1

        if message.author in ping_cache:
            if len(message.role_mentions) > 0:
                if message.author.guild_permissions.mention_everyone:
                    ping_cache[message.author] += len(message.role_mentions) * 2

            if len(message.mentions) > 0:
                if message.author == message.guild.owner:
                    return

                ping_cache[message.author] += len(message.mentions)/2

                if message.author in message.mentions:
                    ping_cache[message.author] -= 0.5

            if "@everyone" in message.content.lower() or "@here" in message.content.lower():
                if message.author == message.guild.owner:
                    return

                if message.author.guild_permissions.mention_everyone:
                    ping_cache[message.author] += 11


            if ping_cache[message.author] > PING_TRESHOLD:
                logger.info("boom")
                ping_cache[message.author] = 0
                if message.author == message.guild.owner:
                    return

                users = db["users"]
                user_data = users.find_one({"id": message.author.id, "guild_id": message.guild.id})

                if not user_data:
                    user_data = CONSTANTS.user_data_template(message.author.id, message.guild.id)
                    users.insert_one(user_data)

                if "whitelisted" in user_data:
                    if user_data["whitelisted"]:
                        return


                guilds = db["guilds"]
                data = guilds.find_one({"id": message.guild.id})

                if not data:
                    data = CONSTANTS.guild_data_template(message.guild.id)
                    guilds.insert_one(data)

                if not "security" in data:
                    return

                if "anti_massping" not in data["security"]["antinuke"]:
                    return

                if not data["security"]["antinuke"]["anti_massping"]:
                    return

                await message.delete()

                embed = discord.Embed(
                    title="AntiSpam Warning",
                    description=f"**{message.author.mention}** has triggered the antispam system, last message: `{message.content}`",
                    color=discord.Color.orange()
                )

                try:
                    message.channel.send(embed=embed)
                except:
                    pass

                log_channel = message.guild.get_channel(data["log_channel"])

                if log_channel != None:
                    await log_channel.send(embed=embed)

                try:
                    try:
                        embed = discord.Embed(
                            title="You have been kicked",
                            description=f"You have been kicked from **{message.guild.name}** for mass pinging",
                            color=discord.Color.red()
                        )

                        await message.author.send(embed=embed)
                    except:
                        pass

                    await message.author.kick(reason="AntiNuke Alert - Mass pinging")
                    ban_cache[self.bot.user] = 0

                    embed = discord.Embed(
                        title="User Kicked",
                        description=f"**{message.author.mention}** has been kicked for mass pinging",
                        color=discord.Color.red()
                    )

                    if log_channel != None:
                        await log_channel.send(embed=embed)
                except discord.Forbidden:
                    embed = discord.Embed(
                        title="AntiNuke Error",
                        description=f"I was unable to kick the user {message.author.mention}",
                        color=discord.Color.red()
                    )

                    if log_channel != None:
                        await log_channel.send(embed=embed)

                    try:
                        guild_owner = message.guild.owner
                        await guild_owner.send(embed=embed)
                    except discord.Forbidden:
                        embed = discord.Embed(
                            title="AntiNuke Error",
                            description=f"Unable to alert the guild owner using DMs",
                            color=discord.Color.red()
                        )

                        if log_channel != None:
                            await log_channel.send(embed=embed)
        else:
            ping_cache[message.author] = 0

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role) -> None:
        if role.permissions.administrator:
            guilds = db["guilds"]
            guild = guilds.find_one({"id": role.guild.id})

            if not guild:
                guild = CONSTANTS.guild_data_template(role.guild.id)
                guilds.insert_one(guild)

            if guild and "security" in guild and "antinuke" in guild["security"]:
                antinuke = guild["security"]["antinuke"]
                if antinuke.get("anti_danger_perms", False):
                    discord_guild = role.guild
                    user = None

                    async for entry in discord_guild.audit_logs(action=discord.AuditLogAction.role_create, limit=2):
                        if entry.target == role:
                            user = entry.user

                    if user == discord_guild.owner:
                        return

                    users = db["users"]
                    user_data = users.find_one({"id": user.id, "guild_id": role.guild.id})

                    if not user_data:
                        user_data = CONSTANTS.user_data_template(user.id, role.guild.id)
                        users.insert_one(user_data)

                    if "whitelisted" in user_data:
                        if user_data["whitelisted"]:
                            embed = discord.Embed(
                                title="AntiNuke Warning",
                                description=f"**{user.mention}** created a dangerous role",
                                color=discord.Color.orange()
                            )

                            log_channel = role.guild.get_channel(guild["log_channel"])

                            if log_channel is None:
                                return

                            await log_channel.send(embed=embed)
                            return

                    await role.delete()

                    log_channel = role.guild.get_channel(guild["log_channel"])

                    if log_channel is None:
                        return

                    embed = discord.Embed(
                        title="AntiNuke Alert",
                        description=f"**{user.mention}** tried to create a dangerous role!",
                        color=discord.Color.red()
                    )

                    await log_channel.send(embed=embed)


    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role) -> None:
        if after.permissions.administrator and not before.permissions.administrator:
            guilds = db["guilds"]
            guild = guilds.find_one({"id": after.guild.id})

            if not guild:
                guild = CONSTANTS.guild_data_template(after.guild.id)
                guilds.insert_one(guild)

            if guild and "security" in guild and "antinuke" in guild["security"]:
                antinuke = guild["security"]["antinuke"]
                if antinuke.get("anti_danger_perms", False):
                    discord_guild = before.guild
                    user = None

                    async for entry in discord_guild.audit_logs(action=discord.AuditLogAction.role_update, limit=2):
                        if entry.target == before or after:
                            if user == discord_guild.owner:
                                continue
                            user = entry.user

                    if user == discord_guild.owner:
                        return

                    if not user:
                        return

                    users = db["users"]
                    user_data = users.find_one({"id": user.id, "guild_id": after.guild.id})

                    if not user_data:
                        user_data = CONSTANTS.user_data_template(user.id, after.guild.id)
                        users.insert_one(user_data)

                    if "whitelisted" in user_data:
                        if user_data["whitelisted"]:
                            embed = discord.Embed(
                                title="AntiNuke Warning",
                                description=f"**{user.mention}** gave **{after.mention}** dangerous permissions",
                                color=discord.Color.orange()
                            )

                            log_channel = after.guild.get_channel(guild["log_channel"])

                            if log_channel is None:
                                return

                            await log_channel.send(embed=embed)
                            return

                    await after.edit(permissions=before.permissions)

                    log_channel = after.guild.get_channel(guild["log_channel"])

                    if log_channel is None:
                        return

                    embed = discord.Embed(
                        title="AntiNuke Alert",
                        description=f"**{user.mention}** tried to give **{after.mention}** dangerous permissions!",
                        color=discord.Color.red()
                    )

                    await log_channel.send(embed=embed)

                    embed = discord.Embed(
                        title="Role Changes Reverted",
                        description=f"**{before.mention}** has been reverted to its previous permissions!",
                        color=discord.Color.green()
                    )

                    await log_channel.send(embed=embed)

                    try:
                        await discord_guild.ban(user, reason="AntiNuke Alert - Dangerous permissions granted")
                        ban_cache[self.bot.user] = 0

                        embed = discord.Embed(
                            title="User Banned",
                            description=f"**{user.mention}** has been banned for trying to give dangerous permissions!",
                            color=discord.Color.red()
                        )

                        if log_channel is not None:
                            await log_channel.send(embed=embed)
                    except discord.Forbidden:
                        embed = discord.Embed(
                            title="AntiNuke Error",
                            description=f"I was unable to ban the user {user.mention}",
                            color=discord.Color.red()
                        )

                        if log_channel is not None:
                            await log_channel.send(embed=embed)

                        try:
                            guild_owner = discord_guild.owner
                            await guild_owner.send(embed=embed)
                        except discord.Forbidden:
                            embed = discord.Embed(
                                title="AntiNuke Error",
                                description=f"Unable to alert the guild owner using DMs",
                                color=discord.Color.red()
                            )

                            if log_channel is not None:
                                await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_ban(self, discord_guild: discord.Guild, banned_user: discord.User) -> None:
        guilds = db["guilds"]
        guild = guilds.find_one({"id": discord_guild.id})

        if not guild:
            guild = CONSTANTS.guild_data_template(discord_guild.id)
            guilds.insert_one(guild)

        if guild and "security" in guild and "antinuke" in guild["security"]:
            antinuke = guild["security"]["antinuke"]
            if antinuke.get("anti_massban", False):
                user = None

                await asyncio.sleep(0.5)

                async for entry in discord_guild.audit_logs(action=discord.AuditLogAction.ban, limit=2):
                    if entry.target == banned_user:
                        user = entry.user

                if not user:
                    return

                if user == discord_guild.owner:
                    return

                users = db["users"]
                user_data = users.find_one({"id": user.id, "guild_id": discord_guild.id})

                if not user_data:
                    user_data = CONSTANTS.user_data_template(user.id, discord_guild.id)
                    users.insert_one(user_data)

                if "whitelisted" in user_data:
                    if user_data["whitelisted"]:
                        return

                over_limit = False

                if user in ban_cache:
                    ban_cache[user] += 1
                    if ban_cache[user] > BAN_TRESHOLD:
                        over_limit = True
                else:
                    ban_cache[user] = 1

                if over_limit:
                    await discord_guild.unban(banned_user, reason="Mass ban detected")
                    ban_cache[self.bot.user] = 0

                    embed = discord.Embed(
                        title="AntiNuke Warning",
                        description=f"**{user.mention}** has triggered the antinuke system, last banned user: **{banned_user.mention}**",
                        color=discord.Color.orange()
                    )

                    log_channel = discord_guild.get_channel(guild["log_channel"])

                    if log_channel != None:
                        await log_channel.send(embed=embed)

                    try:
                        await discord_guild.ban(user, reason="AntiNuke Alert - Mass ban detected")
                        ban_cache[self.bot.user] = 0

                        embed = discord.Embed(
                            title="User Banned",
                            description=f"**{user.mention}** has been banned for trying to mass ban members!",
                            color=discord.Color.red()
                        )

                        if log_channel != None:
                            await log_channel.send(embed=embed)
                    except discord.Forbidden:
                        embed = discord.Embed(
                            title="AntiNuke Error",
                            description=f"I was unable to ban the user {user.mention}",
                            color=discord.Color.red()
                        )

                        if log_channel != None:
                            await log_channel.send(embed=embed)

                        try:
                            guild_owner = discord_guild.owner
                            await guild_owner.send(embed=embed)
                        except discord.Forbidden:
                            embed = discord.Embed(
                                title="AntiNuke Error",
                                description=f"Unable to alert the guild owner using DMs",
                                color=discord.Color.red()
                            )

                            if log_channel != None:
                                await log_channel.send(embed=embed)
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        guilds = db["guilds"]
        guild = guilds.find_one({"id": member.guild.id})

        if not guild:
            guild = CONSTANTS.guild_data_template(member.guild.id)
            guilds.insert_one(guild)

        if guild and "security" in guild and "antinuke" in guild["security"]:
            antinuke = guild["security"]["antinuke"]
            if antinuke.get("anti_masskick", False):
                user = None

                async for entry in member.guild.audit_logs(action=discord.AuditLogAction.kick, limit=2):
                    if entry.target == member:
                        user = entry.user

                if not user:
                    return

                if user == member.guild.owner:
                    return

                users = db["users"]
                user_data = users.find_one({"id": user.id, "guild_id": member.guild.id})

                if not user_data:
                    user_data = CONSTANTS.user_data_template(user.id, member.guild.id)
                    users.insert_one(user_data)

                if "whitelisted" in user_data:
                    if user_data["whitelisted"]:
                        return

                over_limit = False

                if user in kick_cache:
                    kick_cache[user] += 1
                    if kick_cache[user] > KICK_TRESHOLD:
                        over_limit = True
                else:
                    kick_cache[user] = 1

                if over_limit:
                    embed = discord.Embed(
                        title="AntiNuke Warning",
                        description=f"**{user.mention}** has triggered the antinuke system, last kicked user: **{member.mention}**",
                        color=discord.Color.orange()
                    )

                    log_channel = member.guild.get_channel(guild["log_channel"])

                    if log_channel != None:
                        await log_channel.send(embed=embed)

                    try:
                        await member.guild.ban(user, reason="AntiNuke Alert - Mass kick detected")
                        ban_cache[self.bot.user] = 0

                        embed = discord.Embed(
                            title="User Banned",
                            description=f"**{user.mention}** has been banned for trying to mass kick members!",
                            color=discord.Color.red()
                        )

                        if log_channel != None:
                            await log_channel.send(embed=embed)
                    except discord.Forbidden:
                        embed = discord.Embed(
                            title="AntiNuke Error",
                            description=f"I was unable to ban the user {user.mention}",
                            color=discord.Color.red()
                        )

                        if log_channel != None:
                            await log_channel.send(embed=embed)

                        try:
                            guild_owner = member.guild.owner
                            await guild_owner.send(embed=embed)
                        except discord.Forbidden:
                            embed = discord.Embed(
                                title="AntiNuke Error",
                                description=f"Unable to alert the guild owner using DMs",
                                color=discord.Color.red()
                            )

                            if log_channel != None:
                                await log_channel.send(embed=embed)
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.TextChannel) -> None:
        guilds = db["guilds"]
        guild = guilds.find_one({"id": channel.guild.id})

        if not guild:
            guild = CONSTANTS.guild_data_template(channel.guild.id)
            guilds.insert_one(guild)

        if guild and "security" in guild and "antinuke" in guild["security"]:
            antinuke = guild["security"]["antinuke"]
            if antinuke.get("anti_massdelete", False):
                user = None

                async for entry in channel.guild.audit_logs(action=discord.AuditLogAction.channel_delete, limit=2):
                    if entry.target.id == channel.id and entry.user:
                        user = entry.user

                if channel.guild in deleted_channels:
                    deleted_channels[channel.guild].append(channel)
                else:
                    deleted_channels[channel.guild] = [channel]

                if not user:
                    return

                if user == self.bot.user:
                    return

                if user == channel.guild.owner:
                    pass

                users = db["users"]
                user_data = users.find_one({"id": user.id, "guild_id": channel.guild.id})

                if not user_data:
                    user_data = CONSTANTS.user_data_template(user.id, channel.guild.id)
                    users.insert_one(user_data)


                if "whitelisted" in user_data:
                    if user_data["whitelisted"]:
                        return

                over_limit = False

                if user in delete_cache:
                    delete_cache[user] += 1
                    if delete_cache[user] > DELETE_TRESHOLD:
                        over_limit = True
                else:
                    delete_cache[user] = 1

                if over_limit:

                    log_channel = channel.guild.get_channel(guild["log_channel"])

                    try:
                        await channel.guild.ban(user, reason="AntiNuke Alert - Mass delete detected")
                        ban_cache[self.bot.user] = 0

                        embed = discord.Embed(
                            title="User Banned",
                            description=f"**{user.mention}** has been banned for trying to mass delete channels!",
                            color=discord.Color.red()
                        )

                        if log_channel != None:
                            await log_channel.send(embed=embed)
                    except discord.Forbidden:
                        embed = discord.Embed(
                            title="AntiNuke Error",
                            description=f"I was unable to ban the user {user.mention}",
                            color=discord.Color.red()
                        )

                        if log_channel != None:
                            await log_channel.send(embed=embed)

                        try:
                            guild_owner = channel.guild.owner
                            await guild_owner.send(embed=embed)
                        except discord.Forbidden:
                            embed = discord.Embed(
                                title="AntiNuke Error",
                                description=f"Unable to alert the guild owner using DMs",
                                color=discord.Color.red()
                            )

                            if log_channel != None:
                                await log_channel.send(embed=embed)

                    embed = discord.Embed(
                        title="AntiNuke Warning",
                        description=f"**{user.mention}** has triggered the antinuke system, last deleted channel: **{channel.mention}** ({channel.name})",
                        color=discord.Color.orange()
                    )

                    if log_channel != None:
                        try:
                            await log_channel.send(embed=embed)
                        except:
                            await channel.guild.owner.send(embed=embed)
                    else:
                        await channel.guild.owner.send(embed=embed)

                    for del_channel in deleted_channels[channel.guild]:
                        if not del_channel in deleted_channels[channel.guild]:
                            return

                        deleted_channels[channel.guild].remove(del_channel)

                        try:
                            new_channel = await del_channel.clone(reason="AntiNuke Alert - Mass delete detected")
                            ban_cache[self.bot.user] = 0

                            embed = discord.Embed(
                                title="Channel Restored",
                                description=f"**{new_channel.mention}** has been restored!",
                                color=discord.Color.green()
                            )

                            if log_channel != None:
                                await log_channel.send(embed=embed)

                            embed = discord.Embed(
                                title="This channel was nuked",
                                description=f"**{new_channel.mention}** was nuked by **{user.mention}**, channel is restored but message log is gone",
                                color=discord.Color.red()
                            )

                            await new_channel.send(embed=embed)

                            await new_channel.edit(position=del_channel.position)

                        except Exception as e:
                            embed = discord.Embed(
                                title="Error",
                                description=f"An error occured while trying to restore channel **{del_channel.name}**",
                                color=discord.Color.red()
                            )

                            embed.add_field(
                                name="Error",
                                value=f"```{e}```"
                            )

                            if log_channel != None:
                                await log_channel.send(embed=embed)

                    await asyncio.sleep(60)
                    deleted_channels[channel.guild].clear()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = await CachedDB.find_one(db["guilds"], {"id": member.guild.id})

        if not guild:
            return

        if "lockdown" not in guild:
            return

        if guild["lockdown"]:
            await member.kick(reason="Guild is in lockdown")

    @commands.hybrid_group(
        name="whitelist",
        description="Whitelist users from security measures (guild owner only)"
    )
    async def whitelist(self, context: Context) -> None:
        embed = discord.Embed(
            title="Whitelist",
            description="Commands"
        )

        # get all subcommands in group

        subcommands = [cmd for cmd in self.whitelist.walk_commands()]

        data = []

        for subcommand in subcommands:
            description = subcommand.description.partition("\n")[0]
            data.append(f"{await self.bot.get_prefix(context)}whitelist {subcommand.name} - {description}")

        help_text = "\n".join(data)
        embed = discord.Embed(
            title=f"Help: Whitelist", description="List of available commands:", color=0xBEBEFE
        )
        embed.add_field(
            name="Commands", value=f"```{help_text}```", inline=False
        )

        await context.send(embed=embed)

    @whitelist.command(
        name="add",
        description="Whitelist a user from security measures (guild owner only)",
        usage="whitelist add <user>"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def add(self, context: Context, user: discord.Member) -> None:
        guild_owner = context.guild.owner

        if context.author != guild_owner and context.author.id != int(os.getenv("OWNER_ID")):
            await context.send("You must be the guild owner to use this command!")
            return

        users = db["users"]
        user_data = users.find_one({"id": user.id, "guild_id": context.guild.id})

        if not user:
            user_data = CONSTANTS.user_data_template(user.id, context.guild.id)
            users.insert_one(user_data)

        newdata = {
            "$set": {
                "whitelisted": True
            }
        }

        users.update_one({"id": user.id, "guild_id": context.guild.id}, newdata)

        await context.send(f"Whitelisted {user.mention}")

    @whitelist.command(
        name="remove",
        description="Remove a user from the whitelist (guild owner only)",
        usage="whitelist remove <user>"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def remove(self, context: Context, user: discord.Member) -> None:
        guild_owner = context.guild.owner

        if context.author != guild_owner:
            await context.send("You must be the guild owner to use this command!")
            return

        users = db["users"]
        user_data = users.find_one({"id": user.id, "guild_id": context.guild.id})

        if not user:
            user_data = CONSTANTS.user_data_template(user.id, context.guild.id)
            users.insert_one(user_data)

        newdata = {
            "$set": {
                "whitelisted": False
            }
        }

        users.update_one({"id": user.id, "guild_id": context.guild.id}, newdata)

        await context.send(f"Unwhitelisted {user.mention}")

    @whitelist.command(
        name="list",
        description="List all whitelisted users (guild owner only)",
        usage="whitelist list"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def list(self, context: Context) -> None:
        users = db["users"]

        whitelisted = users.find({"guild_id": context.guild.id, "whitelisted": True})

        list = "```"

        for user in whitelisted:
            user = context.guild.get_member(user["id"])
            list += f"{user.name}\n"

        list += "```"

        embed = discord.Embed(
            title="Whitelisted Users",
            description=list
        )

        await context.send(embed=embed)

    @commands.hybrid_group(
        name="trusted",
        description="Trusted users can bypass security measures and change security settings"
    )
    async def trusted(self, context: Context) -> None:
        embed = discord.Embed(
            title="Trusted",
            description="Commands"
        )

        # get all subcommands in group

        subcommands = [cmd for cmd in self.trusted.walk_commands()]

        data = []

        for subcommand in subcommands:
            description = subcommand.description.partition("\n")[0]
            data.append(f"{await self.bot.get_prefix(context)}trusted {subcommand.name} - {description}")

        help_text = "\n".join(data)
        embed = discord.Embed(
            title=f"Help: Trusted", description="List of available commands:", color=0xBEBEFE
        )
        embed.add_field(
            name="Commands", value=f"```{help_text}```", inline=False
        )

        await context.send(embed=embed)

    @trusted.command(
        name="add",
        description="Trust a user (guild owner only)",
        usage="trusted add <user>"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def trusted_add(self, context: Context, user: discord.Member) -> None:
        guild_owner = context.guild.owner

        if context.author != guild_owner and context.author.id != int(os.getenv("OWNER_ID")):
            await context.send("You must be the guild owner to use this command!")
            return

        users = db["users"]
        user_data = users.find_one({"id": user.id, "guild_id": context.guild.id})

        if not user:
            user_data = CONSTANTS.user_data_template(user.id, context.guild.id)
            users.insert_one(user_data)

        newdata = {
            "$set": {
                "trusted": True
            }
        }

        users.update_one({"id": user.id, "guild_id": context.guild.id}, newdata)

        await context.send(f"Trusted {user.mention}")

    @trusted.command(
        name="remove",
        description="Remove a trusted user (guild owner only)",
        usage="trusted remove <user>"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def trusted_remove(self, context: Context, user: discord.Member) -> None:
        guild_owner = context.guild.owner

        if context.author != guild_owner:
            await context.send("You must be the guild owner to use this command!")
            return

        users = db["users"]
        user_data = users.find_one({"id": user.id, "guild_id": context.guild.id})

        if not user:
            user_data = CONSTANTS.user_data_template(user.id, context.guild.id)
            users.insert_one(user_data)

        newdata = {
            "$set": {
                "trusted": False
            }
        }

        users.update_one({"id": user.id, "guild_id": context.guild.id}, newdata)

        await context.send(f"Untrusted {user.mention}")

    @trusted.command(
        name="list",
        description="List all trusted users",
        usage="trusted list"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def trusted_list(self, context: Context) -> None:
        users = db["users"]

        whitelisted = users.find({"guild_id": context.guild.id, "trusted": True})

        list = "```"

        for user in whitelisted:
            user = context.guild.get_member(user["id"])
            list += f"{user.name}\n"

        list += "```"

        embed = discord.Embed(
            title="Trusted Users",
            description=list
        )

        await context.send(embed=embed)

    @commands.hybrid_group(
        name="antinuke",
        description="Commands to manage antinuke (guild owner/trusted only)",
        usage="antinuke <subcommand>"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def antinuke(self, context: Context) -> None:
        embed = discord.Embed(
            title="Antinuke",
            description="Commands"
        )

        # get all subcommands in group

        subcommands = [cmd for cmd in self.antinuke.walk_commands()]

        data = []

        for subcommand in subcommands:
            description = subcommand.description.partition("\n")[0]
            data.append(f"{await self.bot.get_prefix(context)}antinuke {subcommand.name} - {description}")

        help_text = "\n".join(data)
        embed = discord.Embed(
            title=f"Help: Antinuke", description="List of available commands:", color=0xBEBEFE
        )
        embed.add_field(
            name="Commands", value=f"```{help_text}```", inline=False
        )

        await context.send(embed=embed)

    @antinuke.command(
        name="anti_danger_perms",
        description="Prevent someone from giving dangerous perms to @everyone (guild owner/trusted only)",
        usage="antinuke anti_danger_perms <true/false>"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def anti_danger_perms(self, context: Context, enabled: bool) -> None:
        guild_owner = context.guild.owner

        if context.author != guild_owner:
            users = db["users"]
            user_data = users.find_one({"id": context.author.id, "guild_id": context.guild.id})

            if not user_data:
                user_data = CONSTANTS.user_data_template(context.author.id, context.guild.id)
                users.insert_one(user_data)

            if "trusted" in user_data:
                if not user_data["trusted"]:
                    await context.send("You must be the guild owner or trusted to use this command!")
                    return
            else:
                return

        guilds = db["guilds"]
        guild = guilds.find_one({"id": context.guild.id})

        if not guild:
            guild = CONSTANTS.guild_data_template(context.guild.id)
            guilds.insert_one(guild)

        if "security" not in guild:
            newdata = {
                "$set": {
                    "security": {
                        "antinuke": {
                            "anti_danger_perms": enabled,
                            "anti_massban": False,
                            "anti_masskick": False,
                            "anti_masscreate": False,
                            "anti_massdelete": False,
                            "anti_massping": False,
                            "anti_webhook_spam": False

                        }
                    }
                }
            }

            guilds.update_one({"id": context.guild.id}, newdata)
        else:
            newdata = {
                "$set": {
                    "security.antinuke.anti_danger_perms": enabled
                }
            }

            guilds.update_one({"id": context.guild.id}, newdata)

        await context.send(f"Set `anti_danger_perms` to `{enabled}`")

    @antinuke.command(
        name="anti_massban",
        description="Prevent someone from mass banning members (guild owner/trusted only)",
        usage="antinuke anti_massban <true/false>"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def anti_massban(self, context: Context, enabled: bool) -> None:
        guild_owner = context.guild.owner

        if context.author != guild_owner:
            users = db["users"]
            user_data = users.find_one({"id": context.author.id, "guild_id": context.guild.id})

            if not user_data:
                user_data = CONSTANTS.user_data_template(context.author.id, context.guild.id)
                users.insert_one(user_data)

            if "trusted" in user_data:
                if not user_data["trusted"]:
                    await context.send("You must be the guild owner or trusted to use this command!")
                    return
            else:
                return

        guilds = db["guilds"]
        guild = guilds.find_one({"id": context.guild.id})

        if not guild:
            guild = CONSTANTS.guild_data_template(context.guild.id)
            guilds.insert_one(guild)

        if "security" not in guild:
            newdata = {
                "$set": {
                    "security": {
                        "antinuke": {
                            "anti_danger_perms": False,
                            "anti_massban": enabled,
                            "anti_masskick": False,
                            "anti_masscreate": False,
                            "anti_massdelete": False,
                            "anti_massping": False,
                            "anti_webhook_spam": False
                        }
                    }
                }
            }

            guilds.update_one({"id": context.guild.id}, newdata)
        else:
            newdata = {
                "$set": {
                    "security.antinuke.anti_massban": enabled
                }
            }

            guilds.update_one({"id": context.guild.id}, newdata)

        await context.send(f"Set `anti_massban` to `{enabled}`")

    @antinuke.command(
        name="anti_masskick",
        description="Prevent someone from mass kicking members (guild owner/trusted only)",
        usage="antinuke anti_masskick <true/false>"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def anti_masskick(self, context: Context, enabled: bool) -> None:
        guild_owner = context.guild.owner

        if context.author != guild_owner:
            users = db["users"]
            user_data = users.find_one({"id": context.author.id, "guild_id": context.guild.id})

            if not user_data:
                user_data = CONSTANTS.user_data_template(context.author.id, context.guild.id)
                users.insert_one(user_data)

            if "trusted" in user_data:
                if not user_data["trusted"]:
                    await context.send("You must be the guild owner or trusted to use this command!")
                    return
            else:
                return


        guilds = db["guilds"]
        guild = guilds.find_one({"id": context.guild.id})

        if not guild:
            guild = CONSTANTS.guild_data_template(context.guild.id)
            guilds.insert_one(guild)

        if "security" not in guild:
            newdata = {
                "$set": {
                    "security": {
                        "antinuke": {
                            "anti_danger_perms": False,
                            "anti_massban": False,
                            "anti_masskick": enabled,
                            "anti_masscreate": False,
                            "anti_massdelete": False,
                            "anti_massping": False,
                            "anti_webhook_spam": False
                        }
                    }
                }
            }

            guilds.update_one({"id": context.guild.id}, newdata)
        else:
            newdata = {
                "$set": {
                    "security.antinuke.anti_masskick": enabled
                }
            }

            guilds.update_one({"id": context.guild.id}, newdata)

        await context.send(f"Set `anti_masskick` to `{enabled}`")

    @antinuke.command(
        name="anti_massdelete",
        description="Prevent someone from mass deleting channels (guild owner/trusted only)",
        usage="antinuke anti_massdelete <true/false>"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def anti_massdelete(self, context: Context, enabled: bool) -> None:
        guild_owner = context.guild.owner

        if context.author != guild_owner:
            users = db["users"]
            user_data = users.find_one({"id": context.author.id, "guild_id": context.guild.id})

            if not user_data:
                user_data = CONSTANTS.user_data_template(context.author.id, context.guild.id)
                users.insert_one(user_data)

            if "trusted" in user_data:
                if not user_data["trusted"]:
                    await context.send("You must be the guild owner or trusted to use this command!")
                    return
            else:
                return

        guilds = db["guilds"]
        guild = guilds.find_one({"id": context.guild.id})

        if not guild:
            guild = CONSTANTS.guild_data_template(context.guild.id)
            guilds.insert_one(guild)

        if "security" not in guild:
            newdata = {
                "$set": {
                    "security": {
                        "antinuke": {
                            "anti_danger_perms": False,
                            "anti_massban": False,
                            "anti_masskick": False,
                            "anti_masscreate": False,
                            "anti_massdelete": enabled,
                            "anti_massping": False,
                            "anti_webhook_spam": False
                        }
                    }
                }
            }

            guilds.update_one({"id": context.guild.id}, newdata)
        else:
            newdata = {
                "$set": {
                    "security.antinuke.anti_massdelete": enabled
                }
            }

            guilds.update_one({"id": context.guild.id}, newdata)

        await context.send(f"Set `anti_massdelete` to `{enabled}`")

    @antinuke.command(
        name="anti_massping",
        description="Prevent mass pinging (guild owner/trusted only)",
        usage="antinuke anti_massping <true/false>"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def massping(self, context: Context, enabled: bool) -> None:
        guild_owner = context.guild.owner

        if context.author != guild_owner:

            users = db["users"]
            user_data = users.find_one({"id": context.author.id, "guild_id": context.guild.id})

            if not user_data:
                user_data = CONSTANTS.user_data_template(context.author.id, context.guild.id)
                users.insert_one(user_data)

            if "trusted" in user_data:
                if not user_data["trusted"]:
                    await context.send("You must be the guild owner or trusted to use this command!")
                    return
            else:
                return

        guilds = db["guilds"]
        guild = guilds.find_one({"id": context.guild.id})

        if not guild:
            guild = CONSTANTS.guild_data_template(context.guild.id)
            guilds.insert_one(guild)

        if "security" not in guild:
            newdata = {
                "$set": {
                    "security": {
                        "antinuke": {
                            "anti_danger_perms": False,
                            "anti_massban": False,
                            "anti_masskick": False,
                            "anti_masscreate": False,
                            "anti_massdelete": False,
                            "anti_massping": enabled,
                            "anti_webhook_spam": False
                        }
                    }
                }
            }

            guilds.update_one({"id": context.guild.id}, newdata)
        else:
            newdata = {
                "$set": {
                    "security.antinuke.anti_massping": enabled
                }
            }

            guilds.update_one({"id": context.guild.id}, newdata)

        await context.send(f"Set `anti_massping` to `{enabled}`")

    @antinuke.command(
        name="anti_webhook_spam",
        description="Prevent webhook spam (guild owner/trusted only)",
        usage="antinuke anti_webhook_spam <true/false>"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def anti_webhook_spam(self, context: Context, enabled: bool) -> None:
        guild_owner = context.guild.owner

        if context.author != guild_owner:

            users = db["users"]
            user_data = users.find_one({"id": context.author.id, "guild_id": context.guild.id})

            if not user_data:
                user_data = CONSTANTS.user_data_template(context.author.id, context.guild.id)
                users.insert_one(user_data)

            if "trusted" in user_data:
                if not user_data["trusted"]:
                    await context.send("You must be the guild owner or trusted to use this command!")
                    return
            else:
                return

        guilds = db["guilds"]
        guild = guilds.find_one({"id": context.guild.id})

        if not guild:
            guild = CONSTANTS.guild_data_template(context.guild.id)
            guilds.insert_one(guild)

        if "security" not in guild:
            newdata = {
                "$set": {
                    "security": {
                        "antinuke": {
                            "anti_danger_perms": False,
                            "anti_massban": False,
                            "anti_masskick": False,
                            "anti_masscreate": False,
                            "anti_massdelete": False,
                            "anti_massping": False,
                            "anti_webhook_spam": enabled
                        }
                    }
                }
            }

            guilds.update_one({"id": context.guild.id}, newdata)
        else:
            newdata = {
                "$set": {
                    "security.antinuke.anti_webhook_spam": enabled
                }
            }

            guilds.update_one({"id": context.guild.id}, newdata)

        await context.send(f"Set `anti_webhook_spam` to `{enabled}`")

    @commands.hybrid_command(
        name="lockdown",
        description="Lockdown the server (guild owner/trusted only)",
        usage="lockdown"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def lockdown(self, context: Context) -> None:
        guild_owner = context.guild.owner

        if context.author != guild_owner:

            users = db["users"]
            user_data = users.find_one({"id": context.author.id, "guild_id": context.guild.id})

            if not user_data:
                user_data = CONSTANTS.user_data_template(context.author.id, context.guild.id)
                users.insert_one(user_data)

            if "trusted" in user_data:
                if not user_data["trusted"]:
                    await context.send("You must be the guild owner or trusted to use this command!")
                    return
            else:
                return

        guilds = db["guilds"]
        guild = guilds.find_one({"id": context.guild.id})

        if not guild:
            guild = CONSTANTS.guild_data_template(context.guild.id)
            guilds.insert_one(guild)

        embed = discord.Embed(
            title = "Confirm Action",
            description = "Are you sure you want to lockdown the server?",
            color = discord.Color.red()
        )

        await context.send(embed=embed, view=ConfirmView("lockdown", context.author))

    @commands.hybrid_command(
        name="unlockdown",
        description="Unlockdown the server (guild owner/trusted only)",
        usage="unlockdown"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def unlockdown(self, context: Context) -> None:
        guild_owner = context.guild.owner

        try:
            await context.send("Starting Unlockdown")
        except:
            pass

        if context.author != guild_owner:
            users = db["users"]
            user_data = users.find_one({"id": context.author.id, "guild_id": context.guild.id})

            if not user_data:
                user_data = CONSTANTS.user_data_template(context.author.id, context.guild.id)
                users.insert_one(user_data)

            if "trusted" in user_data:
                if not user_data["trusted"]:
                    await context.send("You must be the guild owner or trusted to use this command!")
                    return
            else:
                return

        guilds = db["guilds"]
        guild_data = guilds.find_one({"id": context.guild.id})

        if not guild_data:
            guild_data = CONSTANTS.guild_data_template(context.guild.id)
            guilds.insert_one(guild_data)

        if "oldperms" in guild_data:
            for channel in context.guild.text_channels:
                try:
                    channel_id_str = str(channel.id)
                    if channel_id_str in guild_data["oldperms"]:
                        # Deserialize the permissions
                        perms_dict = guild_data["oldperms"][channel_id_str]
                        overwrite = discord.PermissionOverwrite(**perms_dict)

                        await channel.set_permissions(context.guild.default_role, overwrite=overwrite)
                except:
                    try:
                        await context.send("Failed to change perms for channel " + channel.name)
                    except:
                        pass

            guilds.update_one({"id": context.guild.id}, {"$unset": {"oldperms": ""}})

        guilds.update_one({"id": context.guild.id}, {"$set": {"lockdown": False}})
        await context.send("Server unlockdown complete.")


class ConfirmView(discord.ui.View):
    def __init__(self, value: str, author: discord.Member):
        super().__init__()

        self.value = value
        self.author = author

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.author != interaction.user:
            return interaction.response.send_message("no", ephemeral=True)

        await interaction.response.defer()

        if self.value == "lockdown":
            await interaction.message.edit(content="Locking down the server...", view=None, embed=None)

            oldperms = {}

            for channel in interaction.guild.text_channels:
                try:
                    overwrite = channel.overwrites_for(interaction.guild.default_role)
                    # Serialize the PermissionOverwrite object
                    perms_dict = {perm: value for perm, value in overwrite}

                    oldperms[str(channel.id)] = perms_dict

                    overwrite.send_messages = False
                    await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
                except:
                    pass

            newdata = {
                "$set": {
                    "lockdown": True,
                    "oldperms": oldperms
                }
            }

            guilds = db["guilds"]
            guilds.update_one({"id": interaction.guild.id}, newdata)

            await interaction.message.edit(content="Server lockdown complete.", view=None, embed=None)


    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.primary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.author != interaction.user:
            return interaction.response.send_message("no", ephemeral=True)

        await interaction.response.edit_message("Action cancelled", view=None)



async def setup(bot) -> None:
    await bot.add_cog(Security(bot))
