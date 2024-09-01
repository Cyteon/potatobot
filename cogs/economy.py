# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon

import random
import discord
import time

from discord import ui
from discord.ext import commands
from discord.ext.commands import Context

from utils import CONSTANTS, DBClient, CachedDB, Checks
from ui.farm import FarmButton
from ui.gambling import GamblingButton

db = DBClient.db

class Economy(commands.Cog, name="🪙 Economy"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="balance",
        aliases=["wallet", "bal"],
        description="See yours or someone else's wallet",
        usage="balance [optional: user]"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @commands.cooldown(3, 10, commands.BucketType.user)
    async def wallet(self, context: Context, user: discord.Member = None) -> None:
        if not user:
            user = context.author

        c = db["users"]
        data = c.find_one({"id": user.id, "guild_id": context.guild.id})

        if not data:
            data = CONSTANTS.user_data_template(user.id, context.guild.id)
            c.insert_one(data)
        await context.send(f"**{user}** has ${data['wallet']} in their wallet")

    @commands.hybrid_command(
        name="daily",
        description="Get your daily cash",
        usage="daily"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    async def daily(self, context: Context) -> None:
        c = db["users"]
        data = await CachedDB.find_one(c, {"id": context.author.id, "guild_id": context.guild.id})

        if not data:
            data = CONSTANTS.user_data_template(context.author.id, context.guild.id)
            c.insert_one(data)
        if time.time() - data["last_daily"] < 86400:
            eta = data["last_daily"] + 86400
            await context.send(
                f"You can claim your daily cash <t:{int(eta)}:R>"
            )
            return

        guild = db["guilds"]
        guild_data = await CachedDB.find_one(guild, {"id": context.guild.id})

        if not guild_data:
            guild_data = CONSTANTS.guild_data_template(context.guild.id)
            guild.insert_one(guild_data)

        data["wallet"] += guild_data["daily_cash"]
        newdata = {
            "$set": {"wallet": data["wallet"], "last_daily": time.time()}
        }

        await CachedDB.update_one(c, {"id": context.author.id, "guild_id": context.guild.id}, newdata)

        await context.send(f"Added {guild_data['daily_cash']}$ to wallet")

    @commands.hybrid_command(
        name="rob",
        description="Rob someone's wallet",
        usage="rob <user>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def rob(self, context: Context, user: discord.Member) -> None:
        if user == context.author:
            await context.send("You can't rob yourself")
            return

        c = db["users"]

        target_data = await CachedDB.find_one(c, {"id": user.id, "guild_id": context.guild.id})

        if not target_data:
            return await context.send("User has no money")

        if target_data["wallet"] == 0:
            return await context.send("User has no money")

        author_data = await CachedDB.find_one(c, {"id": context.author.id, "guild_id": context.guild.id})

        if not author_data:
            author_data = CONSTANTS.user_data_template(context.author.id, context.guild.id)
            c.insert_one(author_data)

        max_payout = target_data["wallet"] // 5

        if target_data["last_robbed_at"] > time.time() - 10800:
            eta = target_data["last_robbed_at"] + 10800
            await context.send(
                f"This user can be robbed again <t:{int(eta)}:R>"
            )
            return

        result = random.randint(0, 2)
        if result == 0:
            payout = random.randint(1, max_payout)
            author_data["wallet"] += payout
            target_data["wallet"] -= payout

            newdata = {
                "$set": {
                    "wallet": author_data["wallet"],
                }
            }

            newdata2 = {
                "$set": {
                    "wallet": target_data["wallet"],
                    "last_robbed_at": time.time()
                }
            }

            await CachedDB.update_one(c, {"id": context.author.id, "guild_id": context.guild.id}, newdata)
            await CachedDB.update_one(c, {"id": user.id, "guild_id": context.guild.id}, newdata2)

            await context.send(f"You successfully robbed {user} and got {payout}$")
        elif result == 1:
            payout = min(random.randint(1, max_payout//2), author_data["wallet"]//3, 10000)
            author_data["wallet"] -= payout
            target_data["wallet"] += payout

            newdata = {
                "$set": {
                    "wallet": author_data["wallet"],
                }
            }

            newdata2 = {
                "$set": {"wallet": target_data["wallet"], "last_robbed_at": time.time()}
            }

            await CachedDB.update_one(c, {"id": context.author.id, "guild_id": context.guild.id}, newdata)
            await CachedDB.update_one(c, {"id": user.id, "guild_id": context.guild.id}, newdata2)

            await context.send(f"You got caught by {user} and they took {payout}$")
        else:
            await context.send(f"You failed to rob {user}, but lost nothing")

    @commands.hybrid_command(
        name="baltop",
        description="See the top 10 richest users",
        usage="baltop"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    async def baltop(self, context: Context) -> None:
        c = db["users"]
        data = c.find({"guild_id": context.guild.id}).sort("wallet", -1).limit(10)

        embed = discord.Embed(
            title="Top Balances",
            description="",
            color=discord.Color.gold(),
        )

        i = 1
        for _, user in enumerate(data, start=1):
            member = context.guild.get_member(user["id"])
            if member != None:
                if member.bot:
                    continue
                embed.add_field(
                    name=f"{i}. {member.nick if member.nick else member.display_name if member.display_name else member.name}",
                    value=f"${user['wallet']}",
                    inline=False,
                )
                i += 1

        await context.send(embed=embed)

    @commands.hybrid_command(
        name="pay",
        description="Pay someone from your wallet",
        usage="pay <user> <amount>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    async def pay(self, context: Context, user: discord.Member, amount: int) -> None:
        if amount < 0:
            await context.send("You can't pay a negative amount")
            return

        if user == context.author:
            await context.send("You can't pay yourself")
            return

        c = db["users"]
        data = await CachedDB.find_one(c, {"id": context.author.id, "guild_id": context.guild.id})

        if not data:
            data = CONSTANTS.user_data_template(context.author.id, context.guild.id)
            c.insert_one(data)
        if data["wallet"] < amount:
            await context.send("You don't have enough money")
            return

        target_user_data = c.find_one({"id": user.id, "guild_id": context.guild.id})
        if not target_user_data:
            target_user_data = CONSTANTS.user_data_template(user.id, context.guild.id)

            c.insert_one(target_user_data)
        data["wallet"] -= amount
        target_user_data["wallet"] += amount
        newdata = {
            "$set": {"wallet": data["wallet"]}
        }
        newdata2 = {
            "$set": {"wallet": target_user_data["wallet"]}
        }

        await CachedDB.update_one(c, {"id": context.author.id, "guild_id": context.guild.id}, newdata)
        await CachedDB.update_one(c, {"id": user.id, "guild_id": context.guild.id}, newdata2)

        await context.send(f"Paid {amount}$ to {user.mention}")

    @commands.hybrid_command(
        name="set",
        description="Set someones wallet (admin only)",
        usage="set <user> <amount>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @commands.has_permissions(manage_messages=True)
    async def set(self, context: Context, user: discord.Member, amount: int) -> None:
        c = db["users"]

        target_user_data = await CachedDB.find_one(c, {"id": user.id, "guild_id": context.guild.id})

        if not target_user_data:
            target_user_data = CONSTANTS.user_data_template(context.author.id, context.guild.id)

            c.insert_one(target_user_data)

        newdata = {
            "$set": {"wallet": amount}
        }

        await CachedDB.update_one(c, {"id": user.id, "guild_id": context.guild.id}, newdata)

        await context.send(f"Set {user.mention}'s wallet to {amount}$")

    @commands.hybrid_command(
        name="gamble",
        description="Gamble your money",
        usage="gamble <amount>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    async def gamble(self, context: Context, amount: int) -> None:
        if amount < 0:
            await context.send("You can't gamble a negative amount")
            return

        c = db["users"]
        data = await CachedDB.find_one(c, {"id": context.author.id, "guild_id": context.guild.id})

        if not data:
            data = CONSTANTS.user_data_template(context.author.id, context.guild.id)
            c.insert_one(data)
        if data["wallet"] < amount:
            await context.send("You don't have enough money")
            return

        if amount < 1:
            await context.send("You can't gamble less than 1$")
            return

        await context.send(
            "How would you like to gamble?",
            view=GamblingButton(amount, context.author.id),
        )

    # TODO: MORE CACHING AFTER THIS POINT

    @commands.hybrid_command(
        name="farm",
        description="Farm some potatoes",
        usage="farm"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    async def farm(self, context: Context) -> None:

        c = db["users"]
        data = await CachedDB.find_one(c, {"id": context.author.id, "guild_id": context.guild.id})

        if not data:
            data = CONSTANTS.user_data_template(context.author.id, context.guild.id)
            c.insert_one(data)

        if not "farm" in data:
            data["farm"] = {
                "saplings": 0,
                "crops": 0,
                "harvestable": 0,
                "ready_in": 0
            }
            newdata = {
                "$set": {"farm": data["farm"]}
            }
            c.update_one(
                {"id": context.author.id, "guild_id": context.guild.id}, newdata
            )

        farmData = data["farm"]

        if farmData["ready_in"] < time.time():
            farmData["harvestable"] += farmData["crops"]
            farmData["crops"] = 0

        embed = discord.Embed(
            title="Farm",
            description="Buy saplings to farm potatoes",
            color=0x77dd77,
        )

        embed.add_field(
            name="Saplings",
            value=farmData["saplings"],
            inline=False,
        )

        embed.add_field(
            name="Crops",
            value=farmData["crops"],
            inline=False,
        )

        embed.add_field(
            name="Harvestable",
            value=farmData["harvestable"],
            inline=False,
        )

        embed.add_field(
            name="Ready",
            value=f"<t:{int(farmData['ready_in'])}:R>",
            inline=False,
        )

        embed.set_footer(text=f"Wallet: ${data['wallet']}")

        await context.send(embed=embed, view=FarmButton(context.author.id))

        new_data = {
            "$set": {"farm": farmData}
        }
        c.update_one(
            {"id": context.author.id, "guild_id": context.guild.id}, new_data
        )

async def setup(bot) -> None:
    await bot.add_cog(Economy(bot))
