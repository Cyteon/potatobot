# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon

import random
import pymongo

import discord
from discord.ext import commands
from discord.ext.commands import Context

from easy_pil import *

from utils import CONSTANTS, DBClient, Checks, CachedDB

db = DBClient.db

class Level(commands.Cog, name="🚀 Level"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="level",
        description="See yours or someone elses current level and xp",
        usage="level [optional: user]"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @commands.cooldown(3, 10, commands.BucketType.user)
    async def level(self, context: Context, user: discord.Member = None) -> None:
        if not user:
            user = context.author

        c = db["users"]
        data = await CachedDB.find_one(c, {"id": user.id, "guild_id": context.guild.id})

        if data:
            xp_for_next_level = CONSTANTS.LEVELS_AND_XP[data["level"] + 1]

            percentage = round(data["xp"] / xp_for_next_level * 100, 1)

            background = Editor(Canvas((900, 300), color="#141414"))
            profile_picture = await load_image_async(str(user.avatar.url))
            profile = Editor(profile_picture).resize((150, 150)).circle_image()

            poppins = Font.poppins(size=40)
            poppins_small = Font.poppins(size=30)

            card_right_shape = [(600, 0), (750, 300), (900, 300), (900, 0)]

            background.polygon(card_right_shape, color="#FFFFFF")
            background.paste(profile, (30, 30))

            background.rectangle((30, 220), width=650, height=40, color="#FFFFFF", radius=20)
            background.bar((30, 220), max_width=650, height=40, percentage=percentage, color="orange", radius=20)
            background.text((200, 40), user.name, font=poppins, color="#FFFFFF")

            background.rectangle((200, 100), width=350, height=2, fill="#FFFFFF")
            background.text((200, 130), f"Level {data['level']} - {data['xp']}/{xp_for_next_level} XP", font=poppins_small, color="#FFFFFF")

            file = discord.File(fp=background.image_bytes, filename="level_card.png")
            await context.send(file=file)

        else:
            await context.send("Start chatting to gain a level")

    @commands.hybrid_command(
        name="leaderboard",
        description="See the top 10 users with the most xp in this server",
        usage="leaderboard"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def leaderboard(self, context: Context) -> None:
        c = db["users"]
        data = c.find({"guild_id": context.guild.id}).sort([("level", pymongo.DESCENDING), ("xp", pymongo.DESCENDING)]).limit(10)

        embed = discord.Embed(
            title="Leaderboard",
            description="",
            color=discord.Color.gold()
        )

        for index, user in enumerate(data, start=1):
            member = context.guild.get_member(user["id"])
            if member != None:
                if member.bot:
                    continue
                embed.add_field(
                    name=f"{index}. {member.nick if member.nick else member.display_name if member.display_name else member.name}",
                    value=f"Level: {user['level']} - XP: {user['xp']}",
                    inline=False
                )

        await context.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.guild == None:
            return

        if message.author == self.bot or message.author.bot:
            return

        author = message.author

        c = db["users"]
        data = await CachedDB.find_one(c, {"id": author.id, "guild_id": message.guild.id})

        if not data:
            data = CONSTANTS.user_data_template(author.id, message.guild.id)
            c.insert_one(data)

        if data["level"] >= CONSTANTS.MAX_LEVEL:
            return

        if data["xp"] >= CONSTANTS.MAX_XP:
            return

        data["xp"] += random.randint(1, 3)

        if data["xp"] >= CONSTANTS.LEVELS_AND_XP[data["level"] + 1]:
            guilds = db["guilds"]
            guild_data = await CachedDB.find_one(guilds, {"id": message.guild.id})

            if not guild_data:
                guild_data = CONSTANTS.guild_data_template(message.guild.id)
                guilds.insert_one(guild_data)

            data["level"] += 1
            data["xp"] = 0

            if str(data["level"]) in guild_data["level_roles"]:
                role = message.guild.get_role(guild_data["level_roles"][str(data["level"])])
                await message.author.add_roles(role)

            channel = message.channel
            if guild_data:
                if "level_announce_channel" in guild_data:
                    if guild_data["level_announce_channel"] != 0:
                        channel = message.guild.get_channel(guild_data["level_announce_channel"])

                if "should_announce_levelup" in guild_data:
                    if guild_data["should_announce_levelup"]:
                        await channel.send(f"{author.mention} leveled up to level {data['level']}!")
                else:
                    await channel.send(f"{author.mention} leveled up to level {data['level']}!")

        newdata = {"$set": {"xp": data["xp"], "level": data["level"]}}

        await CachedDB.update_one(c, {"id": author.id, "guild_id": message.guild.id}, newdata)

    @commands.hybrid_command(
        name="create-level-roles",
        description="Create roles for levels (manage_roles permission)",
        usage="create-level-roles"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @commands.has_permissions(manage_roles=True)
    async def create_level_roles(self, context: Context):
        # create role for level 1/3/5/10/15/20

        guilds = db["guilds"]
        guild_data = await CachedDB.find_one(guilds, {"id": context.guild.id})

        if not guild_data:
            guild_data = CONSTANTS.guild_data_template(context.guild.id)
            guilds.insert_one(guild_data)

        for level in [1, 3, 5, 10, 15, 20]:
            if str(level) not in guild_data["level_roles"]:
                role = await context.guild.create_role(name=f"Level {level}")
                guild_data["level_roles"][str(level)] = role.id

        newdata = {"$set": {"level_roles": guild_data["level_roles"]}}

        await CachedDB.update_one(guilds, {"id": context.guild.id}, newdata)
        await context.send("Roles created!")

    @commands.hybrid_command(
        name="delete-level-roles",
        description="Delete roles for levels",
        usage="delete-level-roles"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @commands.has_permissions(manage_roles=True)
    async def delete_level_roles(self, context: Context):
        guilds = db["guilds"]
        guild_data = await CachedDB.find_one(guilds, {"id": context.guild.id})

        if not guild_data:
            guild_data = CONSTANTS.guild_data_template(context.guild.id)
            guilds.insert_one(guild_data)

        for level in guild_data["level_roles"]:
            role = context.guild.get_role(guild_data["level_roles"][level])
            if role:
                try:
                    await role.delete()
                except:
                    pass

        newdata = {"$set": {"level_roles": {}}}

        await CachedDB.update_one(guilds, {"id": context.guild.id}, newdata)
        await context.send("Roles deleted!")

async def setup(bot) -> None:
    await bot.add_cog(Level(bot))
