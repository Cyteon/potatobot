# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon

from datetime import datetime
import random
import asyncio
import discord
import time
from discord.ext import commands
from discord.ext.commands import Context
from utils import CONSTANTS, DBClient, CachedDB, Checks

from discord.ui import Button, button, View

db = DBClient.db["users"]

class Economy(commands.Cog, name="🪙 Economy"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="wallet",
        aliases=["balance", "bal"],
        description="See yours or someone else's wallet",
        usage="wallet [optional: user]"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def wallet(self, context: Context, user: discord.Member = None) -> None:
        if not user:
            user = context.author

        #data = await CachedDB.find_one(db, {"id": user.id, "guild_id": context.guild.id})
        data = db.find_one({"id": user.id, "guild_id": context.guild.id})

        if not data:
            data = CONSTANTS.user_data_template(user.id, context.guild.id)
            db.insert_one(data)
        await context.send(f"**{user}** has ${data['wallet']} in their wallet")

    @commands.hybrid_command(
        name="daily",
        description="Get your daily cash",
        usage="daily"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def daily(self, context: Context) -> None:

        data = await CachedDB.find_one(db, {"id": context.author.id, "guild_id": context.guild.id})

        if not data:
            data = CONSTANTS.user_data_template(context.author.id, context.guild.id)
            db.insert_one(data)
        if time.time() - data["last_daily"] < 86400:
            eta = data["last_daily"] + 86400
            await context.send(
                f"You can claim your daily cash <t:{int(eta)}:R>"
            )
            return

        guild = DBClient.client.potatobot["guilds"]
        guild_data = await CachedDB.find_one(guild, {"id": context.guild.id})

        if not guild_data:
            guild_data = CONSTANTS.guild_data_template(context.guild.id)
            guild.insert_one(guild_data)

        data["wallet"] += guild_data["daily_cash"]
        newdata = {
            "$set": {"wallet": data["wallet"], "last_daily": time.time()}
        }

        await CachedDB.update_one(db, {"id": context.author.id, "guild_id": context.guild.id}, newdata)

        await context.send(f"Added {guild_data['daily_cash']}$ to wallet")

    @commands.hybrid_command(
        name="baltop",
        description="See the top 10 richest users",
        usage="baltop"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def baltop(self, context: Context) -> None:
        data = db.find({"guild_id": context.guild.id}).sort("wallet", -1).limit(10)

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
    async def pay(self, context: Context, user: discord.Member, amount: int) -> None:
        if amount < 0:
            await context.send("You can't pay a negative amount")
            return

        if user == context.author:
            await context.send("You can't pay yourself")
            return

        data = await CachedDB.find_one(db, {"id": context.author.id, "guild_id": context.guild.id})

        if not data:
            data = CONSTANTS.user_data_template(context.author.id, context.guild.id)
            db.insert_one(data)
        if data["wallet"] < amount:
            await context.send("You don't have enough money")
            return

        target_user_data = db.find_one({"id": user.id, "guild_id": context.guild.id})
        if not target_user_data:
            target_user_data = CONSTANTS.user_data_template(context.author.id, context.guild.id)

            db.insert_one(target_user_data)
        data["wallet"] -= amount
        target_user_data["wallet"] += amount
        newdata = {
            "$set": {"wallet": data["wallet"]}
        }
        newdata2 = {
            "$set": {"wallet": target_user_data["wallet"]}
        }

        await CachedDB.update_one(db, {"id": context.author.id, "guild_id": context.guild.id}, newdata)
        await CachedDB.update_one(db, {"id": user.id, "guild_id": context.guild.id}, newdata2)

        await context.send(f"Paid {amount}$ to {user.mention}")

    @commands.hybrid_command(
        name="set",
        description="Set someones wallet (admin only)",
        usage="set <user> <amount>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_messages=True)
    async def set(self, context: Context, user: discord.Member, amount: int) -> None:
        target_user_data = await CachedDB.find_one(db, {"id": user.id, "guild_id": context.guild.id})

        if not target_user_data:
            target_user_data = CONSTANTS.user_data_template(context.author.id, context.guild.id)

            db.insert_one(target_user_data)

        newdata = {
            "$set": {"wallet": amount}
        }

        await CachedDB.update_one(db, {"id": user.id, "guild_id": context.guild.id}, newdata)

        await context.send(f"Set {user.mention}'s wallet to {amount}$")

    @commands.hybrid_command(
        name="gamble",
        description="Gamble your money",
        usage="gamble <amount>"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def gamble(self, context: Context, amount: int) -> None:
        if amount < 0:
            await context.send("You can't gamble a negative amount")
            return

        data = await CachedDB.find_one(db, {"id": context.author.id, "guild_id": context.guild.id})

        if not data:
            data = CONSTANTS.user_data_template(context.author.id, context.guild.id)
            db.insert_one(data)
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

    # TODO: MORE CACHING AFTER HERE

    @commands.hybrid_command(
        name="farm",
        description="Farm some potatoes",
        usage="farm"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def farm(self, context: Context) -> None:
        data = db.find_one({"id": context.author.id, "guild_id": context.guild.id})
        if not data:
            data = CONSTANTS.user_data_template(context.author.id, context.guild.id)
            db.insert_one(data)

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
            db.update_one(
                {"id": context.author.id, "guild_id": context.guild.id}, newdata
            )

        farmData = data["farm"]

        if farmData["ready_in"] < time.time():
            farmData["harvestable"] += farmData["crops"]
            farmData["crops"] = 0

        embed = discord.Embed(
            title="Farm",
            description="Buy saplings to farm potatoes",
            color=discord.Color.green(),
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
            name="Ready in",
            value=f"<t:{int(farmData['ready_in'])}:R>",
            inline=False,
        )

        embed.set_footer(text=f"Wallet: ${data['wallet']}")

        await context.send(embed=embed, view=FarmButton(context.author.id))

        new_data = {
            "$set": {"farm": farmData}
        }
        db.update_one(
            {"id": context.author.id, "guild_id": context.guild.id}, new_data
        )



class FarmButton(View):
    def __init__(self, authorid):
        super().__init__(timeout=None)
        self.saplings = 0
        self.authorid = authorid

    @button(label="Buy Saplings (100$/20)", style=discord.ButtonStyle.primary, custom_id="farm",emoji="🌱")
    async def farm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.authorid:
            return await interaction.response.send_message("You can't farm someone else's farm", ephemeral=True)

        data = db.find_one({"id": interaction.user.id, "guild_id": interaction.guild.id})
        if not data:
            data = CONSTANTS.user_data_template(interaction.user.id, interaction.guild.id)
            db.insert_one(data)

        if data["wallet"] < 100:
            await interaction.response.send_message("You don't have enough money", ephemeral=True)
            return

        data["wallet"] -= 100

        data["farm"]["saplings"] += 20
        newdata = {
            "$set": {
                "wallet": data["wallet"],
                "farm.saplings": data["farm"]["saplings"]
                }
        }
        db.update_one(
            {"id": interaction.user.id, "guild_id": interaction.guild.id}, newdata
        )

        await interaction.response.send_message("You bought saplings for 100$", ephemeral=True)

        farmData = data["farm"]

        embed = discord.Embed(
            title="Farm",
            description="Buy saplings to farm potatoes",
            color=discord.Color.green(),
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
            name="Ready in",
            value=f"<t:{int(farmData['ready_in'])}:R>",
            inline=False,
        )

        embed.set_footer(text=f"Wallet: ${data['wallet']}")

        await interaction.message.edit(embed=embed, view=FarmButton(self.authorid))

    @button(label="Buy Saplings for all money", style=discord.ButtonStyle.primary, custom_id="farmall",emoji="🌱")
    async def farmall(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.authorid:
            return await interaction.response.send_message("You can't farm someone else's farm", ephemeral=True)

        data = db.find_one({"id": interaction.user.id, "guild_id": interaction.guild.id})
        if not data:
            data = CONSTANTS.user_data_template(interaction.user.id, interaction.guild.id)
            db.insert_one(data)

        data["farm"]["saplings"] += int(0.2*data["wallet"])
        wallet = data["wallet"]

        data["wallet"] = 0


        newdata = {
            "$set": {
                "wallet": data["wallet"],
                "farm.saplings": data["farm"]["saplings"]
                }
        }
        db.update_one(
            {"id": interaction.user.id, "guild_id": interaction.guild.id}, newdata
        )

        await interaction.response.send_message(f"You bought {0.2*wallet} saplings for ${wallet}", ephemeral=True)

        farmData = data["farm"]

        embed = discord.Embed(
            title="Farm",
            description="Buy saplings to farm potatoes",
            color=discord.Color.green(),
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
            name="Ready in",
            value=f"<t:{int(farmData['ready_in'])}:R>",
            inline=False,
        )

        embed.set_footer(text=f"Wallet: ${data['wallet']}")

        await interaction.message.edit(embed=embed, view=FarmButton(self.authorid))

    @button(label="Plant Crops", style=discord.ButtonStyle.primary, custom_id="plant",emoji="🌾", row=1)
    async def plant(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.authorid:
            return await interaction.response.send_message("You can't plant someone else's crops", ephemeral=True)

        data = db.find_one({"id": interaction.user.id, "guild_id": interaction.guild.id})
        if not data:
            data = CONSTANTS.user_data_template(interaction.user.id, interaction.guild.id)
            db.insert_one(data)

        farmData = data["farm"]

        if not farmData["saplings"] > 0:
            await interaction.response.send_message("You don't have any saplings to plant", ephemeral=True)
            return

        if farmData["crops"] > 0:
            await interaction.response.send_message("You already have crops growing", ephemeral=True)
            return

        farmData["crops"] = farmData["saplings"]
        farmData["ready_in"] = time.time() + 86400
        farmData["saplings"] = 0

        newdata = {
            "$set": {
                "farm.saplings": farmData["saplings"],
                "farm.crops": farmData["crops"],
                "farm.ready_in": farmData["ready_in"],
                }
        }
        db.update_one(
            {"id": interaction.user.id, "guild_id": interaction.guild.id}, newdata
        )

        await interaction.response.send_message("You planted your crops", ephemeral=True)

        farmData = data["farm"]

        embed = discord.Embed(
            title="Farm",
            description="Buy saplings to farm potatoes",
            color=discord.Color.green(),
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
            name="Ready in",
            value=f"<t:{int(farmData['ready_in'])}:R>",
            inline=False,
        )

        embed.set_footer(text=f"Wallet: ${data['wallet']}")

        await interaction.message.edit(embed=embed, view=FarmButton(self.authorid))

    @button(label="Harvest Crops", style=discord.ButtonStyle.primary, custom_id="harvest",emoji="🥔", row=1)
    async def harvest(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.authorid:
            return await interaction.response.send_message("You can't harvest someone else's crops", ephemeral=True)

        data = db.find_one({"id": interaction.user.id, "guild_id": interaction.guild.id})
        if not data:
            data = CONSTANTS.user_data_template(interaction.user.id, interaction.guild.id)
            db.insert_one(data)

        farmData = data["farm"]

        if not farmData["harvestable"] > 0:
            await interaction.response.send_message("You don't have any crops to harvest", ephemeral=True)
            return

        await interaction.response.send_message("You harvested your crops for $" + str(farmData["harvestable"]*10), ephemeral=True)

        data["wallet"] += farmData["harvestable"]*10

        if farmData["ready_in"] < time.time():
            farmData["harvestable"] = 0
            farmData["ready_in"] = time.time() + 86400

        newdata = {
            "$set": {
                "wallet": data["wallet"],
                "farm.harvestable": 0,
                "farm.ready_in": farmData["ready_in"],
                }
        }
        db.update_one(
            {"id": interaction.user.id, "guild_id": interaction.guild.id}, newdata
        )


        farmData = data["farm"]

        embed = discord.Embed(
            title="Farm",
            description="Buy saplings to farm potatoes",
            color=discord.Color.green(),
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
            name="Ready in",
            value=f"<t:{int(farmData['ready_in'])}:R>",
            inline=False,
        )

        embed.set_footer(text=f"Wallet: ${data['wallet']}")

        await interaction.message.edit(embed=embed, view=FarmButton(self.authorid))

class GamblingButton(View):
    def __init__(self, amount, authorid):
        super().__init__(timeout=None)
        self.amount = amount
        self.authorid = authorid

    @button(label="Coin Flip", style=discord.ButtonStyle.primary, custom_id="coin_flip", emoji="🪙")
    async def coinflip(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.authorid:
            return await interaction.response.send_message("Nuh uh :D", ephemeral=True)

        await interaction.response.edit_message(content="Heads or tails?", view=HeadsOrTailsButton(self.amount, self.authorid))

    @button(label="Dice Roll", style=discord.ButtonStyle.primary, custom_id="roll_dice", emoji="🎲")
    async def diceroll(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.authorid:
            return await interaction.response.send_message("Nuh uh :D", ephemeral=True)

        await interaction.response.edit_message(content="Choose a number between 1 and 6", view=RollButton(self.amount, self.authorid))

    @button(label="Blackjack", style=discord.ButtonStyle.primary, custom_id="blackjack", emoji="🃏")
    async def blackjack(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.authorid:
            return await interaction.response.send_message("Nuh uh :D", ephemeral=True)

        view = BlackjackView(self.amount, self.authorid)
        await view.start_game(interaction)

class BlackjackView(View):
    def __init__(self, amount, authorid):
        super().__init__(timeout=None)
        self.amount = amount
        self.authorid = authorid
        self.deck = self.create_deck()
        self.player_hand = [self.deck.pop(), self.deck.pop()]
        self.dealer_hand = [self.deck.pop(), self.deck.pop()]
        self.player_score = self.calculate_score(self.player_hand)
        self.dealer_score = self.calculate_score(self.dealer_hand)
        self.game_over = False

    def create_deck(self):
        deck = []
        for _ in range(4):
            for value in range(1, 14):
                deck.append(value)
        random.shuffle(deck)
        return deck

    def calculate_score(self, hand):
        score = 0
        aces = 0
        for card in hand:
            if card == 1:
                aces += 1
            elif card > 10:
                score += 10
            else:
                score += card
        for _ in range(aces):
            if score + 11 <= 21:
                score += 11
            else:
                score += 1
        return score

    def update_embed(self):
        embed = discord.Embed(title="Blackjack", color=discord.Color.green())
        embed.add_field(name="Your hand", value=f"{self.player_hand} ({self.player_score})", inline=False)
        embed.add_field(name="Dealer's hand", value=f"{self.dealer_hand[0]} and hidden", inline=False)  # Show one dealer card
        return embed

    @button(label="Hit", style=discord.ButtonStyle.primary, custom_id="hit", emoji="👊")
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.authorid:
            return await interaction.response.send_message("Nuh uh :D", ephemeral=True)

        if self.game_over:
            return await interaction.response.send_message("The game is over", ephemeral=True)

        user = db.find_one({"id": interaction.user.id, "guild_id": interaction.guild.id})

        self.player_hand.append(self.deck.pop())
        self.player_score = self.calculate_score(self.player_hand)

        if self.player_score > 21:
            self.game_over = True
            user["wallet"] -= self.amount

            newdata = {"$set": {"wallet": user["wallet"]}}
            db.update_one({"id": interaction.user.id, "guild_id": interaction.guild.id}, newdata)

            embed = self.update_embed()
            return await interaction.response.edit_message(content="You went over 21! You lost", embed=embed, view=self)

        if self.player_score == 21:
            self.game_over = True
            user["wallet"] += self.amount

            newdata = {"$set": {"wallet": user["wallet"]}}
            db.update_one({"id": interaction.user.id, "guild_id": interaction.guild.id}, newdata)

            embed = self.update_embed()
            return await interaction.response.edit_message(content="You got 21! You won", embed=embed, view=self)

        embed = self.update_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @button(label="Stand", style=discord.ButtonStyle.primary, custom_id="stand", emoji="🛑")
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.authorid:
            return await interaction.response.send_message("Nuh uh :D", ephemeral=True)

        if self.game_over:
            return await interaction.response.send_message("The game is over", ephemeral=True)

        user = db.find_one({"id": interaction.user.id, "guild_id": interaction.guild.id})

        while self.dealer_score < 17:
            self.dealer_hand.append(self.deck.pop())
            self.dealer_score = self.calculate_score(self.dealer_hand)

        if self.dealer_score > 21:
            self.game_over = True
            user["wallet"] += self.amount

            newdata = {"$set": {"wallet": user["wallet"]}}
            db.update_one({"id": interaction.user.id, "guild_id": interaction.guild.id}, newdata)

            embed = self.update_embed()
            return await interaction.response.edit_message(content="Dealer went over 21! You won", embed=embed, view=self)

        if self.dealer_score > self.player_score:
            self.game_over = True
            user["wallet"] -= self.amount

            newdata = {"$set": {"wallet": user["wallet"]}}
            db.update_one({"id": interaction.user.id, "guild_id": interaction.guild.id}, newdata)

            embed = self.update_embed()
            return await interaction.response.edit_message(content="Dealer won", embed=embed, view=self)

        if self.dealer_score == self.player_score:
            self.game_over = True
            embed = self.update_embed()
            return await interaction.response.edit_message(content="It's a tie", embed=embed, view=self)

        self.game_over = True
        embed = self.update_embed()
        await interaction.response.edit_message(content="Game is over", embed=embed, view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.authorid

    async def on_timeout(self):
        self.clear_items()
        self.stop()

    async def start_game(self, interaction: discord.Interaction):
        embed = self.update_embed()
        await interaction.response.send_message(embed=embed, view=self)

class HeadsOrTailsButton(View):
    def __init__(self, amount, authorid):
        super().__init__(timeout=None)
        self.amount = amount
        self.authorid = authorid

    @button(label="Heads", style=discord.ButtonStyle.primary, custom_id="heads",emoji="🪙")
    async def heads(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.authorid:
            return

        await interaction.response.defer()
        await interaction.message.edit(content="Flipping the coin...", view=None)
        await asyncio.sleep(1)
        coin = random.choice(["heads", "tails"])

        data = db.find_one({"id": interaction.user.id, "guild_id": interaction.guild.id})

        if coin == "heads":
            await interaction.message.edit(content=f"The coin landed on {coin}! You won {self.amount * 2}$")

            data["wallet"] += self.amount * 2
        else:
            await interaction.message.edit(content=f"The coin landed on {coin}! You lost {self.amount}$")

            data["wallet"] -= self.amount

        newdata = {
            "$set": {"wallet": data["wallet"]}
        }
        db.update_one(
            {"id": interaction.user.id, "guild_id": interaction.guild.id}, newdata
        )

    @button(label="Tails", style=discord.ButtonStyle.primary, custom_id="tails",emoji="🪙")
    async def tails(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.authorid:
            return

        await interaction.response.defer()
        await interaction.message.edit(content="Flipping the coin...", view=None)
        await asyncio.sleep(1)
        coin = random.choice(["heads", "tails"])

        data = db.find_one({"id": interaction.user.id, "guild_id": interaction.guild.id})

        if coin == "tails":
            await interaction.message.edit(content=f"The coin landed on {coin}! You won {self.amount * 2}$")

            data["wallet"] += self.amount * 2
        else:
            await interaction.message.edit(content=f"The coin landed on {coin}! You lost {self.amount}$")

            data["wallet"] -= self.amount

        newdata = {
            "$set": {"wallet": data["wallet"]}
        }
        db.update_one(
            {"id": interaction.user .id, "guild_id": interaction.guild.id}, newdata
        )

# roll 1 - 6
class RollButton(View):
    def __init__(self, amount, authorid):
        super().__init__(timeout=None)
        self.amount = amount
        self.authorid = authorid

    @button(label="", style=discord.ButtonStyle.primary, custom_id="roll_1",emoji="1️⃣")
    async def one(self, interaction: discord.Interaction, button: button):
        if interaction.user.id != self.authorid:
            return

        await interaction.message.edit(content="Rolling the dice...", view=None)
        await asyncio.sleep(1)
        number = random.randrange(1, 6)

        data = db.find_one({"id": interaction.user.id, "guild_id": interaction.guild.id})

        if number == 1:
            await interaction.message.edit(content=f"The dice landed on {number}! You won {self.amount * 5}$")

            data["wallet"] += self.amount * 5
        else:
            await interaction.message.edit(content=f"The dice landed on {number}! You lost {self.amount}$")

            data["wallet"] -= self.amount

        newdata = {
            "$set": {"wallet": data["wallet"]}
        }
        db.update_one(
            {"id": interaction.user.id, "guild_id": interaction.guild.id}, newdata
        )

    @button(label="", style=discord.ButtonStyle.primary, custom_id="roll_2",emoji="2️⃣")
    async def two(self, interaction: discord.Interaction, button: button):
        if interaction.user.id != self.authorid:
            return

        await interaction.message.edit(content="Rolling the dice...", view=None)
        await asyncio.sleep(1)
        number = random.randrange(1, 6)

        data = db.find_one({"id": interaction.user.id, "guild_id": interaction.guild.id})

        if number == 2:
            await interaction.message.edit(content=f"The dice landed on {number}! You won {self.amount * 5}$")

            data["wallet"] += self.amount * 5
        else:
            await interaction.message.edit(content=f"The dice landed on {number}! You lost {self.amount}$")

            data["wallet"] -= self.amount

        newdata = {
            "$set": {"wallet": data["wallet"]}
        }
        db.update_one(
            {"id": interaction.user.id, "guild_id": interaction.guild.id}, newdata
        )

    @button(label="", style=discord.ButtonStyle.primary, custom_id="roll_3",emoji="3️⃣")
    async def three(self, interaction: discord.Interaction, button: button):
        if interaction.user.id != self.authorid:
            return

        await interaction.message.edit(content="Rolling the dice...", view=None)
        await asyncio.sleep(1)
        number = random.randrange(1, 6)

        data = db.find_one({"id": interaction.user.id, "guild_id": interaction.guild.id})

        if number == 3:
            await interaction.message.edit(content=f"The dice landed on {number}! You won {self.amount * 5}$")

            data["wallet"] += self.amount * 5
        else:
            await interaction.message.edit(content=f"The dice landed on {number}! You lost {self.amount}$")

            data["wallet"] -= self.amount

        newdata = {
            "$set": {"wallet": data["wallet"]}
        }
        db.update_one(
            {"id": interaction.user.id, "guild_id": interaction.guild.id}, newdata
        )

    @button(label="", style=discord.ButtonStyle.primary, custom_id="roll_4",emoji="4️⃣")
    async def four(self, interaction: discord.Interaction, button: button):
        if interaction.user.id != self.authorid:
            return

        await interaction.message.edit(content="Rolling the dice...", view=None)
        await asyncio.sleep(1)
        number = random.randrange(1, 6)

        data = db.find_one({"id": interaction.user.id, "guild_id": interaction.guild.id})

        if number == 4:
            await interaction.message.edit(content=f"The dice landed on {number}! You won {self.amount * 5}$")

            data["wallet"] += self.amount * 5
        else:
            await interaction.message.edit(content=f"The dice landed on {number}! You lost {self.amount}$")

            data["wallet"] -= self.amount

        newdata = {
            "$set": {"wallet": data["wallet"]}
        }
        db.update_one(
            {"id": interaction.user.id, "guild_id": interaction.guild.id}, newdata
        )

    @button(label="", style=discord.ButtonStyle.primary, custom_id="roll_5",emoji="5️⃣")
    async def five(self, interaction: discord.Interaction, button: button):
        if interaction.user.id != self.authorid:
            return


        await interaction.message.edit(content="Rolling the dice...", view=None)
        await asyncio.sleep(1)
        number = random.randrange(1, 6)

        data = db.find_one({"id": interaction.user.id, "guild_id": interaction.guild.id})

        if number == 5:
            await interaction.message.edit(content=f"The dice landed on {number}! You won {self.amount * 5}$")

            data["wallet"] += self.amount * 5
        else:
            await interaction.message.edit(content=f"The dice landed on {number}! You lost {self.amount}$")

            data["wallet"] -= self.amount

        newdata = {
            "$set": {"wallet": data["wallet"]}
        }
        db.update_one(
            {"id": interaction.user.id, "guild_id": interaction.guild.id}, newdata
        )

    @button(label="", style=discord.ButtonStyle.primary, custom_id="roll_6",emoji="6️⃣")
    async def six(self, interaction: discord.Interaction, button: button):

        if interaction.user.id != self.authorid:
            return

        await interaction.message.edit(content="Rolling the dice...", view=None)
        await asyncio.sleep(1)
        number = random.randrange(1, 6)

        data = db.find_one({"id": interaction.user.id, "guild_id": interaction.guild.id})

        if number == 6:
            await interaction.message.edit(content=f"The dice landed on {number}! You won {self.amount * 5}$")

            data["wallet"] += self.amount * 5
        else:
            await interaction.message.edit(content=f"The dice landed on {number}! You lost {self.amount}$")

            data["wallet"] -= self.amount

        newdata = {
            "$set": {"wallet": data["wallet"]}
        }
        db.update_one(
            {"id": interaction.user.id, "guild_id": interaction.guild.id}, newdata
        )




async def setup(bot) -> None:
    await bot.add_cog(Economy(bot))
