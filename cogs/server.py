# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon

import discord
import os
import aiohttp

from cryptography.fernet import Fernet

from discord.ext import commands
from discord.ext.commands import Context

from utils import CachedDB, Checks, DBClient, CONSTANTS
from ui.setup import StartSetupView


db = DBClient.db

class Server(commands.Cog, name="⚙️ Server"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.prefixDB = bot.prefixDB

    @commands.hybrid_command(
        name="setup",
        description="It's setup time!!!!!!",
        usage="testcommand"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def setup(self, context: Context) -> None:
        if context.author.id != context.guild.owner.id:
            await context.send("You must be the owner of the server to run this command.")
            return

        embed = discord.Embed(
            title="Setup",
            description="Let's set up your server!",
            color=0x2F3136
        )

        await context.send(embed=embed, view=StartSetupView(context.guild.id))

    @commands.command(
        name="prefix",
        description="Change the bot prefix",
        usage="prefix <symbol>"
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
        description="Set API key for AI (run in private channel please)",
        usage="groq-api-key <key>"
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

        try:
            await context.message.delete()
        except:
            pass

        if key == "NONE":
            cipher_text = "NONE"

        newdata = { "$set": { "groq_api_key": cipher_text } }

        c.update_one({"id": context.guild.id}, newdata)

        await context.send(f"Set groq api key")

    @commands.hybrid_command(
        name="stealemoji",
        description="Steal an emoji from another server.",
        usage="stealemoji <emoji> <name>"
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
        description="Add an emoji from a URL.",
        usage="emojifromurl <url> <name>"
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

    @commands.hybrid_group(
        name="settings",
        description="Command to change server settings",
        aliases=["setting"],
        usage="settings <subcommand> [args]"
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
        description="Show server settings",
        usage="settings show"
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
        name="announce-levelup",
        description="Should levelups be announced?",
        usage="settings announce-levelup <enabled>"
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
        description="Set daily cash amount",
        usage="settings daily-cash <amount>"
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
        description="Set category where tickets are created",
        usage="settings tickets-category <category>"
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
        description="Set level up announce channel",
        usage="settings level-up-channel <channel>"
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
        description="Set ticket support role",
        usage="settings tickets-support-role <role>"
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
        description="Set log channel",
        usage="settings log-channel <channel>"
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
        description="Set default role to be given to new members",
        usage="settings default-role <role>"
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
        usage="settings level-roles"
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
        description="Show level roles",
        usage="settings level-roles show"
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
        description="Set level roles",
        usage="settings level-roles set <level> <role>"
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

        await context.send(f"Set level {level} role to {role.name}")

    @commands.hybrid_group(
        name="command",
        description="Commands to re-enable/disable commands",
        aliases=["cmd"],
        usage="Command <subcommand> [args]"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_channels=True)
    async def cmd(self, context: Context) -> None:
        prefix = await self.bot.get_prefix(context)

        cmds = "\n".join([f"{prefix}cmd {cmd.name} - {cmd.description}" for cmd in self.cmd.walk_commands()])

        embed = discord.Embed(
            title=f"Help: Command", description="List of available commands:", color=0xBEBEFE
        )
        embed.add_field(
            name="Commands", value=f"```{cmds}```", inline=False
        )

        await context.send(embed=embed)

    @cmd.command(
        name="disable",
        description="Disable a command",
        usage="cmd disable <command>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(administrator=True)
    async def disable(self, context: Context, *, command: str) -> None:
        cmd = self.bot.get_command(command)

        if not cmd:
            return await context.send("Command not found")

        if cmd.qualified_name.startswith("command") or cmd.qualified_name.startswith("cmd"):
            return await context.send("You cannot disable this command")

        guild = await CachedDB.find_one(db["guilds"], {"id": context.guild.id})

        if not guild:
            guild = CONSTANTS.guild_data_template(context.guild.id)
            db["guilds"].insert_one(guild)

        if cmd.qualified_name in guild["disabled_commands"]:
            return await context.send(f"The command `{cmd.qualified_name}` is already disabled")

        guild["disabled_commands"].append(cmd.qualified_name)

        await CachedDB.update_one(db["guilds"], {"id": context.guild.id}, {"$set": {"disabled_commands": guild["disabled_commands"]}})

        await context.send(f"Disabled the command `{cmd.qualified_name}`")

    @cmd.command(
        name="enable",
        description="Re-enable a command",
        usage="cmd enable <command>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(administrator=True)
    async def cmd_enable(self, context: Context, *, command: str) -> None:
        cmd = self.bot.get_command(command)

        if not cmd:
            return await context.send("Command not found")

        guild = await CachedDB.find_one(db["guilds"], {"id": context.guild.id})

        if not guild:
            guild = CONSTANTS.guild_data_template(context.guild.id)
            db["guilds"].insert_one(guild)

        if command not in guild["disabled_commands"]:
            return await context.send(f"The command `{cmd.qualified_name}` is not disabled")

        guild["disabled_commands"].remove(cmd.qualified_name)

        await CachedDB.update_one(db["guilds"], {"id": context.guild.id}, {"$set": {"disabled_commands": guild["disabled_commands"]}})

        await context.send(f"Re-enabled the command `{cmd.qualified_name}`")


async def setup(bot) -> None:
    await bot.add_cog(Server(bot))
