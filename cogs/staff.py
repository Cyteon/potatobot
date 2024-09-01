# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon

import os

import re
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

from utils import DBClient, CONSTANTS, Checks, CachedDB

from ui.recreate import deleteconfirm

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
            color=0xff6961
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
            color=0xfdfd96
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
            description=f"{user.mention} ({user}) left the server",
            color=0xff6961
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
            color=0xff6961
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
            color=0x77dd77
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
            color=0xff6961
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
            color=0xff6961
        )

        c = db["guilds"]
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
            color = 0x77dd77
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
            color = 0xff6961
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

    ###

    @commands.hybrid_command(
        name="kick",
        aliases=["k", "yeet"],
        description="Kick a user out of the server.",
        usage="kick <user> [reason]",
        extras={"example":"kick @user advertising"}
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @Checks.has_perm(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
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
                            color=0xff6961
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
        usage="nick <user> <nickname>",
        extras={"example":"nick @user new nickname"}
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @Checks.has_perm(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def nick(
        self, context: Context, member: discord.Member, *, nickname: str = None
    ) -> None:
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
        aliases=["b"],
        description="Bans a user from the server.",
        usage="ban <user> [reason]",
        extras={"example": "ban @user spamming"},
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @Checks.has_perm(ban_members=True)
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
                    embed = discord.Embed(
                        title="You were banned!",
                        description=f"You were banned from **{context.guild.name}**",
                        color=0xff6961
                    )

                    embed.add_field(name="Reason", value=reason)

                    await member.send(embed=embed)
                    messaged = True
                except:
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
                            color=0xff6961
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
        extras={"example": "hackban 1226487228914602005 spamming"}
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @Checks.has_perm(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def hackban(self, context: Context, user: discord.User, *, reason: str = "Not specified"):
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
        usage="softban <user>",
        extras={"example": "softban @user"}
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @Checks.has_perm(ban_members=True)
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
        usage="unban <user>",
        extras={"example": "unban 1226487228914602005"}
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @Checks.has_perm(ban_members=True)
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
                        embed = discord.Embed(
                            title="You were unbanned!",
                            description=f"You were unbanned from **{context.guild.name}**",
                            color=0x77dd77
                        )

                        await user.send(embed=embed)
                    except:
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
                                color=0x77dd77
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
        aliases=["clear"],
        description="Delete a number of messages.",
        usage="purge <amount>",
        extras={"example": "purge 10"}
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @Checks.has_perm(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @app_commands.describe(amount="The amount of messages that should be deleted.")
    async def purge(self, context: Context, amount: int) -> None:
        await context.defer()
        purged_messages = await context.channel.purge(limit=amount + 1)
        embed = discord.Embed(
            description=f"**{context.author}** cleared **{len(purged_messages)-1}** messages!",
            color=0xBEBEFE,
        )
        await context.channel.send(embed=embed)

    @commands.hybrid_command(
        name="archive",
        description="Archives in a text file the last messages with a chosen limit of messages.",
        usage="archive <limit>",
        extras={"example": "archive 10"}
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @Checks.has_perm(manage_messages=True)
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
        description="Mute a user in the server.",
        usage="mute <user> <time> [reason]",
        extras={"example": "mute @user 1d spamming in #general"}
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @Checks.has_perm(moderate_members=True)
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
        description="Unmute a user in the server.",
        usage="unmute <user> [reason]",
        extras={"example": "unmute @user spamming in #general"}
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @Checks.has_perm(moderate_members=True)
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
        description="Lock a channel.",
        usage="lock [optional: channel]",
        extras={"example": "lock #general"}
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @Checks.has_perm(manage_channels=True)
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
        description="Unlock a channel.",
        usage="unlock [channel]",
        extras={"example": "unlock #general"}
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @Checks.has_perm(manage_channels=True)
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
        name="jail",
        description="Jail a user.",
        usage="jail <user> [reason]",
        extras={"example": "jail @user admin abusing"}
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @Checks.has_perm(manage_roles=True, manage_channels=True, manage_messages=True)
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
        description="Unjail a user.",
        usage="unjail <user>",
        extras={"example": "unjail @user"}
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @Checks.has_perm(manage_roles=True, manage_channels=True, manage_messages=True)
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
        description="Warn a user.",
        usage="warnings add <user> <reason>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @Checks.has_perm(manage_messages=True)
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
        description="Get a user's warnings.",
        usage="warnings list <user>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @Checks.has_perm(manage_messages=True)
    async def listwarnings(self, context: Context, user: discord.Member) -> None:
        users = db["users"]
        data = users.find_one({"id": user.id, "guild_id": context.guild.id})

        if not data:
            data = CONSTANTS.user_data_template(user.id, context.guild.id)
            users.insert_one(data)


        embed = discord.Embed(
            title=f"Warnings for {user}",
            color=0xff6961
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
        description="Clear a user's warnings.",
        usage="warnings clear <user>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @Checks.has_perm(manage_messages=True)
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
        usage="recreate [optional: channel]",
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @Checks.has_perm(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def recreate(self, context: Context, channel: discord.TextChannel = None) -> None:
        if not channel:
            channel = context.channel

        await context.send(f"Are you sure you want to recreate {channel.mention}", view=deleteconfirm(context.author, channel))

async def setup(bot) -> None:
    await bot.add_cog(Staff(bot))
