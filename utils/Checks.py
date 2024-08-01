# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon

import discord
import os
import sys
import json

from utils import DBClient, CONSTANTS, CachedDB

db = DBClient.db

async def is_not_blacklisted(context):

    users_global = db["users_global"]
    user = await CachedDB.find_one(users_global, {"id": context.author.id}, ex=120)

    if user is None:
        user = CONSTANTS.user_global_data_template(context.author.id)
        users_global.insert_one(user)

    if user["blacklisted"]:
        raise discord.ext.commands.CommandError("You are blacklisted from using the bot, reason: **" + (user["blacklist_reason"] if user["blacklist_reason"] else "Not Specified") + "**")
    else:
        return True

# TODO: Make this
# Coming soon
async def has_perm(*argv):
    pass
