# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon

import discord

from utils import DBClient, CONSTANTS, CachedDB, Errors

from discord.ext import commands
from discord.ext.commands import Context

db = DBClient.db

async def is_not_blacklisted(context: Context):
    users_global = db["users_global"]
    user = await CachedDB.find_one(users_global, {"id": context.author.id})

    if user is None:
        user = CONSTANTS.user_global_data_template(context.author.id)
        users_global.insert_one(user)

    if user["blacklisted"]:
        raise Errors.UserBlacklisted("You are blacklisted from using the bot, reason: **" + (user["blacklist_reason"] if user["blacklist_reason"] else "Not Specified") + "**")
    else:
        return True

# TODO: Add fakeperms
def has_perm(**perms):
    def predicate(context: commands.Context):
        author_permissions = context.channel.permissions_for(context.author)

        for perm, value in perms.items():
            if getattr(author_permissions, perm, None) != value:
                raise discord.ext.commands.MissingPermissions([perm])
        return True

    return commands.check(predicate)

async def command_not_disabled(context: Context):
    if context.guild:
        guild = await CachedDB.find_one(db["guilds"], {"id": context.guild.id})

        if guild is None:
            guild = CONSTANTS.guild_data_template(context.guild.id)
            db["guilds"].insert_one(guild)

        if context.command.qualified_name in guild["disabled_commands"] or context.command.qualified_name.split(" ")[0] in guild["disabled_commands"]:
            raise Errors.CommandDisabled("This command is disabled in this server.")
        else:
            return True
    else:
        return True
