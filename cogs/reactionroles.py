# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon

import discord

from discord.ext import commands
from discord.ext.commands import Context

from utils import CachedDB, DBClient

db = DBClient.db

from utils import Checks

class ReactionRoles(commands.Cog, name="🇺🇸 Reaction Roles"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload) -> None:
        message_data = await CachedDB.find_one(db["reactionroles"], {"message_id": payload.message_id})
        if not message_data:
            return

        # Determine the emoji identifier
        if payload.emoji.id is None:
            # This is a Unicode emoji
            emoji_id = str(payload.emoji)
        else:
            # This is a custom emoji
            emoji_id = str(payload.emoji.id)

        if emoji_id not in message_data["roles"]:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        role = guild.get_role(int(message_data["roles"][emoji_id]))
        if not role:
            return

        member = guild.get_member(payload.user_id)
        if not member:
            return

        try:
            await member.add_roles(role)
            print(f"Added role {role.name} to {member.name}")
        except discord.HTTPException as e:
            print(f"Failed to add role: {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload) -> None:
        message_data = await CachedDB.find_one(db["reactionroles"], {"message_id": payload.message_id})
        if not message_data:
            return

        # Determine the emoji identifier
        if payload.emoji.id is None:
            # This is a Unicode emoji
            emoji_id = str(payload.emoji)
        else:
            # This is a custom emoji
            emoji_id = str(payload.emoji.id)

        if emoji_id not in message_data["roles"]:
            try:
                message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
                await message.remove_reaction(payload.emoji, self.bot.get_user(payload.user_id))
            except Exception as e:
                print(e)
                pass
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        role = guild.get_role(int(message_data["roles"][emoji_id]))
        if not role:
            return

        member = guild.get_member(payload.user_id)
        if not member:
            return

        try:
            await member.remove_roles(role)
            print(f"Removed role {role.name} from {member.name}")
        except discord.HTTPException as e:
            print(f"Failed to remove role: {e}")

    @commands.hybrid_group(
        name="reactionroles",
        description="Command to manage reaction roles",
        usage="reactionroles",
        aliases=["rr"]
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @commands.has_permissions(manage_roles=True)
    async def reactionroles(self, context: Context) -> None:
        subcommands = [cmd for cmd in self.reactionroles.walk_commands()]

        data = []

        for subcommand in subcommands:
            description = subcommand.description.partition("\n")[0]
            data.append(f"{await self.bot.get_prefix(context)}reactionroles {subcommand.name} - {description}")

        help_text = "\n".join(data)
        embed = discord.Embed(
            title=f"Help: Reaction Roles", description="List of available commands:", color=0xBEBEFE
        )
        embed.add_field(
            name="Commands", value=f"```{help_text}```", inline=False
        )

        await context.send(embed=embed)

    @reactionroles.command(
        name="add",
        description="Add a reaction role to a message",
        usage="reactionroles add <message_id> <role_id> <emoji>",
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @commands.has_permissions(manage_roles=True)
    async def add(self, context: commands.Context, message_id: str, role: discord.Role, emoji: str):
        try:
            message_id = int(message_id)
        except:
            await context.send("Invalid message ID.")
            return

        try:
            message = await context.channel.fetch_message(message_id)
        except discord.NotFound:
            await context.send("Message not found.")
            return

        # Convert emoji to a format we can use
        try:
            # Try to convert to Discord emoji
            emoji_obj = await commands.EmojiConverter().convert(context, emoji)
            emoji_id = str(emoji_obj.id)
        except commands.BadArgument:
            # If conversion fails, assume it's a Unicode emoji
            emoji_id = emoji

        try:
            await message.add_reaction(emoji)
        except discord.HTTPException:
            await context.send("Failed to add reaction. Make sure the bot has permission to add reactions.")
            return

        message_data = await CachedDB.find_one(db["reactionroles"], {"message_id": message_id})

        if not message_data:
            db["reactionroles"].insert_one({
                "message_id": message_id,
                "roles": {emoji_id: str(role.id)}
            })
            await context.send("Reaction role added.")
        else:
            if emoji_id in message_data["roles"]:
                await context.send("Reaction role already exists.")
            else:
                message_data["roles"][emoji_id] = str(role.id)
                await CachedDB.update_one(db["reactionroles"], {"message_id": message_id}, {"$set": {"roles": message_data["roles"]}})
                await context.send("Reaction role added.")

async def setup(bot) -> None:
    await bot.add_cog(ReactionRoles(bot))
