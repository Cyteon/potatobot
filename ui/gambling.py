import discord
import asyncio
import random

from discord import ui
from discord.ui import Button, button, View

from utils import DBClient

db = DBClient.db

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
        embed = discord.Embed(title="Blackjack", color=0x77dd77)
        embed.add_field(name="Your hand", value=f"{self.player_hand} ({self.player_score})", inline=False)
        embed.add_field(name="Dealer's hand", value=f"{self.dealer_hand[0]} and hidden", inline=False)  # Show one dealer card
        return embed

    @button(label="Hit", style=discord.ButtonStyle.primary, custom_id="hit", emoji="👊")
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.authorid:
            return await interaction.response.send_message("Nuh uh :D", ephemeral=True)

        if self.game_over:
            return await interaction.response.send_message("The game is over", ephemeral=True)

        c = db["users"]
        user = c.find_one({"id": interaction.user.id, "guild_id": interaction.guild.id})

        self.player_hand.append(self.deck.pop())
        self.player_score = self.calculate_score(self.player_hand)

        if self.player_score > 21:
            self.game_over = True
            user["wallet"] -= self.amount

            newdata = {"$set": {"wallet": user["wallet"]}}
            c.update_one({"id": interaction.user.id, "guild_id": interaction.guild.id}, newdata)

            embed = self.update_embed()
            return await interaction.response.edit_message(content="You went over 21! You lost", embed=embed, view=self)

        if self.player_score == 21:
            self.game_over = True
            user["wallet"] += self.amount

            newdata = {"$set": {"wallet": user["wallet"]}}
            c.update_one({"id": interaction.user.id, "guild_id": interaction.guild.id}, newdata)

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

        c = db["users"]
        user = c.find_one({"id": interaction.user.id, "guild_id": interaction.guild.id})

        while self.dealer_score < 17:
            self.dealer_hand.append(self.deck.pop())
            self.dealer_score = self.calculate_score(self.dealer_hand)

        if self.dealer_score > 21:
            self.game_over = True
            user["wallet"] += self.amount

            newdata = {"$set": {"wallet": user["wallet"]}}
            c.update_one({"id": interaction.user.id, "guild_id": interaction.guild.id}, newdata)

            embed = self.update_embed()
            return await interaction.response.edit_message(content="Dealer went over 21! You won", embed=embed, view=self)

        if self.dealer_score > self.player_score:
            self.game_over = True
            user["wallet"] -= self.amount

            newdata = {"$set": {"wallet": user["wallet"]}}
            c.update_one({"id": interaction.user.id, "guild_id": interaction.guild.id}, newdata)

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

        c = db["users"]
        data = c.find_one({"id": interaction.user.id, "guild_id": interaction.guild.id})

        if coin == "heads":
            await interaction.message.edit(content=f"The coin landed on {coin}! You won {self.amount * 2}$")

            data["wallet"] += self.amount * 2
        else:
            await interaction.message.edit(content=f"The coin landed on {coin}! You lost {self.amount}$")

            data["wallet"] -= self.amount

        newdata = {
            "$set": {"wallet": data["wallet"]}
        }
        c.update_one(
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

        c = db["users"]
        data = c.find_one({"id": interaction.user.id, "guild_id": interaction.guild.id})

        if coin == "tails":
            await interaction.message.edit(content=f"The coin landed on {coin}! You won {self.amount * 2}$")

            data["wallet"] += self.amount * 2
        else:
            await interaction.message.edit(content=f"The coin landed on {coin}! You lost {self.amount}$")

            data["wallet"] -= self.amount

        newdata = {
            "$set": {"wallet": data["wallet"]}
        }
        c.update_one(
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

        c = db["users"]
        data = c.find_one({"id": interaction.user.id, "guild_id": interaction.guild.id})

        if number == 1:
            await interaction.message.edit(content=f"The dice landed on {number}! You won {self.amount * 5}$")

            data["wallet"] += self.amount * 5
        else:
            await interaction.message.edit(content=f"The dice landed on {number}! You lost {self.amount}$")

            data["wallet"] -= self.amount

        newdata = {
            "$set": {"wallet": data["wallet"]}
        }
        c.update_one(
            {"id": interaction.user.id, "guild_id": interaction.guild.id}, newdata
        )

    @button(label="", style=discord.ButtonStyle.primary, custom_id="roll_2",emoji="2️⃣")
    async def two(self, interaction: discord.Interaction, button: button):
        if interaction.user.id != self.authorid:
            return

        await interaction.message.edit(content="Rolling the dice...", view=None)
        await asyncio.sleep(1)
        number = random.randrange(1, 6)

        c = db["users"]
        data = c.find_one({"id": interaction.user.id, "guild_id": interaction.guild.id})

        if number == 2:
            await interaction.message.edit(content=f"The dice landed on {number}! You won {self.amount * 5}$")

            data["wallet"] += self.amount * 5
        else:
            await interaction.message.edit(content=f"The dice landed on {number}! You lost {self.amount}$")

            data["wallet"] -= self.amount

        newdata = {
            "$set": {"wallet": data["wallet"]}
        }
        c.update_one(
            {"id": interaction.user.id, "guild_id": interaction.guild.id}, newdata
        )

    @button(label="", style=discord.ButtonStyle.primary, custom_id="roll_3",emoji="3️⃣")
    async def three(self, interaction: discord.Interaction, button: button):
        if interaction.user.id != self.authorid:
            return

        await interaction.message.edit(content="Rolling the dice...", view=None)
        await asyncio.sleep(1)
        number = random.randrange(1, 6)

        c = db["users"]
        data = c.find_one({"id": interaction.user.id, "guild_id": interaction.guild.id})

        if number == 3:
            await interaction.message.edit(content=f"The dice landed on {number}! You won {self.amount * 5}$")

            data["wallet"] += self.amount * 5
        else:
            await interaction.message.edit(content=f"The dice landed on {number}! You lost {self.amount}$")

            data["wallet"] -= self.amount

        newdata = {
            "$set": {"wallet": data["wallet"]}
        }

        c.update_one(
            {"id": interaction.user.id, "guild_id": interaction.guild.id}, newdata
        )

    @button(label="", style=discord.ButtonStyle.primary, custom_id="roll_4",emoji="4️⃣")
    async def four(self, interaction: discord.Interaction, button: button):
        if interaction.user.id != self.authorid:
            return

        await interaction.message.edit(content="Rolling the dice...", view=None)
        await asyncio.sleep(1)
        number = random.randrange(1, 6)

        c = db["users"]
        data = c.find_one({"id": interaction.user.id, "guild_id": interaction.guild.id})

        if number == 4:
            await interaction.message.edit(content=f"The dice landed on {number}! You won {self.amount * 5}$")

            data["wallet"] += self.amount * 5
        else:
            await interaction.message.edit(content=f"The dice landed on {number}! You lost {self.amount}$")

            data["wallet"] -= self.amount

        newdata = {
            "$set": {"wallet": data["wallet"]}
        }

        c.update_one(
            {"id": interaction.user.id, "guild_id": interaction.guild.id}, newdata
        )

    @button(label="", style=discord.ButtonStyle.primary, custom_id="roll_5",emoji="5️⃣")
    async def five(self, interaction: discord.Interaction, button: button):
        if interaction.user.id != self.authorid:
            return

        await interaction.message.edit(content="Rolling the dice...", view=None)
        await asyncio.sleep(1)
        number = random.randrange(1, 6)

        c = db["users"]
        data = c.find_one({"id": interaction.user.id, "guild_id": interaction.guild.id})

        if number == 5:
            await interaction.message.edit(content=f"The dice landed on {number}! You won {self.amount * 5}$")

            data["wallet"] += self.amount * 5
        else:
            await interaction.message.edit(content=f"The dice landed on {number}! You lost {self.amount}$")

            data["wallet"] -= self.amount

        newdata = {
            "$set": {"wallet": data["wallet"]}
        }
        c.update_one(
            {"id": interaction.user.id, "guild_id": interaction.guild.id}, newdata
        )

    @button(label="", style=discord.ButtonStyle.primary, custom_id="roll_6",emoji="6️⃣")
    async def six(self, interaction: discord.Interaction, button: button):

        if interaction.user.id != self.authorid:
            return

        await interaction.message.edit(content="Rolling the dice...", view=None)
        await asyncio.sleep(1)
        number = random.randrange(1, 6)

        c = db["users"]
        data = c.find_one({"id": interaction.user.id, "guild_id": interaction.guild.id})

        if number == 6:
            await interaction.message.edit(content=f"The dice landed on {number}! You won {self.amount * 5}$")

            data["wallet"] += self.amount * 5
        else:
            await interaction.message.edit(content=f"The dice landed on {number}! You lost {self.amount}$")

            data["wallet"] -= self.amount

        newdata = {
            "$set": {"wallet": data["wallet"]}
        }
        c.update_one(
            {"id": interaction.user.id, "guild_id": interaction.guild.id}, newdata
        )
