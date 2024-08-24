import discord
import time

from discord import ui
from discord.ui import button, View, Modal

from utils import DBClient, CachedDB

db = DBClient.db

class FarmModal(Modal, title = "Buy Saplings (5$ per sapling)"):
    def __init__(self, message):
        super().__init__(timeout = 60)

        self.message = message

    amount = ui.TextInput(label = "Amount of Sapling", placeholder = "Type max to buy for all your money", style=discord.TextStyle.short, min_length = 1, max_length = 50)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        users = db["users"]
        data = await CachedDB.find_one(users, {"id": interaction.user.id, "guild_id": interaction.guild.id})

        value = self.amount.value

        if value == "max":
            value = data["wallet"] // 5
        else:
            if not value.isdigit():
                await interaction.response.send_message("Please enter a valid number", ephemeral=True)
                return

        price = 5 * int(value)

        if data["wallet"] < price:
            await interaction.response.send_message(f"You cant afford {value} sapling(s) for ${price}", ephemeral=True)
            return

        data["wallet"] -= price
        data["farm"]["saplings"] += int(value)

        new_data = {
            "$set": {"farm": data["farm"], "wallet": data["wallet"]}
        }

        await CachedDB.update_one(users, {"id": interaction.user.id, "guild_id": interaction.guild.id}, new_data)

        await interaction.response.send_message(f"Bought {value} sapling(s) for ${price}", ephemeral=True)

        c = db["users"]
        data = c.find_one({"id": interaction.user.id, "guild_id": interaction.guild.id})

        farmData = data["farm"]

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

        await interaction.message.edit(embed=embed, view=FarmButton(interaction.user.id))

class FarmButton(View):
    def __init__(self, authorid):
        super().__init__(timeout=None)
        self.saplings = 0
        self.authorid = authorid

    @button(label="Buy Saplings (show menu)", style=discord.ButtonStyle.primary, custom_id="farm",emoji="🌱")
    async def farm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.authorid:
            return await interaction.response.send_message("You can't farm someone else's farm", ephemeral=True)

        await interaction.response.send_modal(FarmModal(interaction.message))


    @button(label="Plant Crops", style=discord.ButtonStyle.primary, custom_id="plant",emoji="🌾", row=1)
    async def plant(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.authorid:
            return await interaction.response.send_message("You can't plant someone else's crops", ephemeral=True)

        c = db["users"]
        data = c.find_one({"id": interaction.user.id, "guild_id": interaction.guild.id})


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
        c.update_one(
            {"id": interaction.user.id, "guild_id": interaction.guild.id}, newdata
        )

        await interaction.response.send_message("You planted your crops", ephemeral=True)

        farmData = data["farm"]

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

        await interaction.message.edit(embed=embed, view=FarmButton(self.authorid))

    @button(label="Harvest Crops", style=discord.ButtonStyle.primary, custom_id="harvest",emoji="🥔", row=1)
    async def harvest(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.authorid:
            return await interaction.response.send_message("You can't harvest someone else's crops", ephemeral=True)

        c = db["users"]
        data = c.find_one({"id": interaction.user.id, "guild_id": interaction.guild.id})

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
        c.update_one(
            {"id": interaction.user.id, "guild_id": interaction.guild.id}, newdata
        )


        farmData = data["farm"]

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

        await interaction.message.edit(embed=embed, view=FarmButton(self.authorid))
