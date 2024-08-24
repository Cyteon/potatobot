import discord
import asyncio

from utils import DBClient

db = DBClient.db

class StartSetupView(discord.ui.View):
    def __init__(self, server_id) -> None:
        super().__init__()
        self.server_id = server_id

    @discord.ui.button(label="Start Setup", style=discord.ButtonStyle.primary)
    async def start_setup(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.user != interaction.guild.owner:
            await interaction.response.send_message("You can't interact with this :D", ephemeral=True)
            return

        embed = discord.Embed(
            title="Would you like to set up the ticket system?",
            description="This will allow people to create tickets for support.",
            color=0x2F3136
        )

        await interaction.response.edit_message(embed=embed, view=TicketSetupView(self.server_id))

class TicketSetupView(discord.ui.View):
    def __init__(self, server_id) -> None:
        super().__init__()
        self.server_id = server_id

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.primary)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.user != interaction.guild.owner:
            await interaction.response.send_message("You can't interact with this :D", ephemeral=True)
            return

        embed = discord.Embed(
            title="What category should the tickets be created in?",
            description="Select the category where the tickets should be created.",
            color=0x2F3136
        )

        categories = [discord.SelectOption(label=category.name, value=category.id) for category in interaction.guild.categories]

        await interaction.response.edit_message(embed=embed, view=TicketCategoryView(self.server_id, categories))

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.secondary)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        embed = discord.Embed(
            title="Change leveling system settings",
            description="Would you like to change the leveling system settings for your server?",
            color=0x2F3136
        )

        await interaction.response.edit_message(embed=embed, view=LevelingSetupView(self.server_id))

class TicketCategorySelect(discord.ui.Select):
    def __init__(self, server_id, categories) -> None:
        super().__init__(placeholder="Choose a category...", options=categories)
        self.server_id = server_id

    async def callback(self, interaction: discord.Interaction) -> None:
        if interaction.user != interaction.guild.owner:
            await interaction.response.send_message("You can't interact with this :D", ephemeral=True)
            return

        category_id = self.values[0]
        db.guilds.update_one({"id": self.server_id}, {"$set": {"tickets_category": int(category_id)}})

        embed = discord.Embed(
            title="What role should be given access to the tickets and pinged?",
            description="This can be a role like `Support` or `Staff`. You can mention the role to select it.",
            color=0x2F3136
        )

        await interaction.response.edit_message(embed=embed, view=None)

        while True:
            try:
                message = await interaction.client.wait_for("message", check=lambda m: m.author == interaction.user, timeout=30)
            except asyncio.TimeoutError:
                await interaction.followup.send("You took too long to respond.", ephemeral=True)
                return

            try:
                role_id = int(message.content.replace("<@&", "").replace(">", ""))
                role = interaction.guild.get_role(role_id)

                if role is None:
                    await interaction.followup.send("You must mention a role.", ephemeral=True)
                    continue
                break
            except:
                await interaction.followup.send("You must mention a role.", ephemeral=True)

        await message.delete()
        db.guilds.update_one({"id": self.server_id}, {"$set": {"tickets_support_role": role_id}})

        embed = discord.Embed(
            title="Change leveling system settings",
            description="Would you like to change the leveling system settings for your server?",
            color=0x2F3136
        )

        await interaction.message.edit(embed=embed, view=LevelingSetupView(self.server_id))

class TicketCategoryView(discord.ui.View):
    def __init__(self, server_id, categories) -> None:
        super().__init__()
        self.server_id = server_id
        self.categories = categories

        self.add_item(TicketCategorySelect(self.server_id, self.categories))

class TicketSupportRoleSelect(discord.ui.Select):
    def __init__(self, server_id, roles) -> None:
        super().__init__(placeholder="Choose a role...", options=roles)
        self.server_id = server_id

    async def callback(self, interaction: discord.Interaction) -> None:
        if interaction.user != interaction.guild.owner:
            await interaction.response.send_message("You can't interact with this :D", ephemeral=True)
            return

        role_id = self.values[0]
        db.guilds.update_one({"id": self.server_id}, {"$set": {"tickets_support_role": role_id}})

        embed = discord.Embed(
            title="Change leveling system settings",
            description="Would you like to change the leveling system settings for your server?",
            color=0x2F3136
        )

        await interaction.response.edit_message(embed=embed, view=LevelingSetupView(self.server_id))

class TicketSupportRoleView(discord.ui.View):
    def __init__(self, server_id, roles) -> None:
        super().__init__()
        self.server_id = server_id

        self.add_item(TicketSupportRoleSelect(self.server_id, roles))

class LevelingSetupView(discord.ui.View):
    def __init__(self, server_id) -> None:
        super().__init__()
        self.server_id = server_id

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.primary)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.user != interaction.guild.owner:
            await interaction.response.send_message("You can't interact with this :D", ephemeral=True)
            return

        embed = discord.Embed(
            title="Should levelups be announced?",
            description="Tell when someone levels up",
            color=0x2F3136
        )

        await interaction.response.edit_message(embed=embed, view=LevelingShouldAnnounceLevelUp(self.server_id))

    @discord.ui.button(label="No", style=discord.ButtonStyle.secondary)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        db.guilds.update_one({"id": self.server_id}, {"$set": {"should_announce_levelup": False}})

        embed = discord.Embed(
            title="Setup starboard?",
            description="Would you like to setup the starboard?",
            color=0x2F3136
        )

        await interaction.response.edit_message(embed=embed, view=StarboardSetupView(self.server_id))

class LevelingShouldAnnounceLevelUp(discord.ui.View):
    def __init__(self, server_id) -> None:
        super().__init__()
        self.server_id = server_id

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.primary)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.user != interaction.guild.owner:
            await interaction.response.send_message("You can't interact with this :D", ephemeral=True)
            return

        db.guilds.update_one({"id": self.server_id}, {"$set": {"should_announce_levelup": True}})

        embed = discord.Embed(
            title="Would you like to set a channel for levelups?",
            description="Which channel to send levelup messages, will be sent in the channel where the user leveled up if not set. Mention the channel to select it.",
            color=0x2F3136
        )

        channels = [discord.SelectOption(label=channel.name, value=channel.id) for channel in interaction.guild.text_channels]

        await interaction.response.edit_message(embed=embed, view=LevelingChannelSelectView(self.server_id, channels))

    @discord.ui.button(label="No", style=discord.ButtonStyle.secondary)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        db.guilds.update_one({"id": self.server_id}, {"$set": {"should_announce_levelup": False}})

        embed = discord.Embed(
            title="Setup starboard?",
            description="Would you like to setup the starboard?",
            color=0x2F3136
        )

        await interaction.response.edit_message(embed=embed, view=StarboardSetupView(self.server_id))

class LevelingChannelSelectView(discord.ui.View):
    def __init__(self, server_id, channels) -> None:
        super().__init__()
        self.server_id = server_id

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.primary)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.user != interaction.guild.owner:
            await interaction.response.send_message("You can't interact with this :D", ephemeral=True)
            return

        embed = discord.Embed(
            title="Mention the channel for levelups",
            description="Which channel to send levelup messages, will be sent in the channel where the user leveled up if not set. Mention the channel.",
            color=0x2F3136
        )

        await interaction.response.edit_message(embed=embed, view=None)

        while True:
            try:
                message = await interaction.client.wait_for("message", check=lambda m: m.author == interaction.user, timeout=30)
            except asyncio.TimeoutError:
                await interaction.followup.send("You took too long to respond.", ephemeral=True)
                return

            try:
                channel_id = int(message.content.replace("<#", "").replace(">", ""))
                channel = interaction.guild.get_channel(channel_id)

                if channel is None:
                    await interaction.followup.send("You must mention a channel.", ephemeral=True)
                    continue
                break
            except:
                await interaction.followup.send("You must mention a channel.", ephemeral=True)

        await message.delete()
        db.guilds.update_one({"id": self.server_id}, {"$set": {"level_announce_channel": channel_id}})

        embed = discord.Embed(
            title="Setup starboard?",
            description="Would you like to setup the starboard?",
            color=0x2F3136
        )

        await interaction.message.edit(embed=embed, view=StarboardSetupView(self.server_id))

    @discord.ui.button(label="No", style=discord.ButtonStyle.secondary)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        embed = discord.Embed(
            title="Setup starboard?",
            description="Would you like to setup the starboard?",
            color=0x2F3136
        )

        await interaction.response.edit_message(embed=embed, view=StarboardSetupView(self.server_id))

class StarboardSetupView(discord.ui.View):
    def __init__(self, server_id) -> None:
        super().__init__()
        self.server_id = server_id

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.primary)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.user != interaction.guild.owner:
            await interaction.response.send_message("You can't interact with this :D", ephemeral=True)
            return

        db.guilds.update_one({"id": self.server_id}, {"$set": {"starboard.enabled": True}})

        embed = discord.Embed(
            title="Mention the channel for the starboard",
            description="Send a message containing the channel where the starboard should be created",
            color=0x2F3136
        )

        await interaction.response.edit_message(embed=embed, view=None)

        while True:
            try:
                message = await interaction.client.wait_for("message", check=lambda m: m.author == interaction.user, timeout=30)
            except asyncio.TimeoutError:
                await interaction.followup.send("You took too long to respond.", ephemeral=True)
                return

            try:
                channel_id = int(message.content.replace("<#", "").replace(">", ""))
                channel = interaction.guild.get_channel(channel_id)

                if channel is None:
                    await interaction.followup.send("You must mention a channel.", ephemeral=True)
                    continue
                break
            except:
                await interaction.followup.send("You must mention a channel.", ephemeral=True)

        await message.delete()
        db.guilds.update_one({"id": self.server_id}, {"$set": {"starboard.channel": channel_id}})

        embed = discord.Embed(
            title="Select the starboard threshold",
            description="Send a message containing the threshold for the starboard.",
            color=0x2F3136
        )

        await interaction.message.edit(embed=embed, view=None)

        while True:
            try:
                message = await interaction.client.wait_for("message", check=lambda m: m.author == interaction.user, timeout=30)
            except asyncio.TimeoutError:
                await interaction.followup.send("You took too long to respond.", ephemeral=True)
                return

            if not message.content.isdigit():
                await interaction.followup.send("You must send a number.", ephemeral=True)
                continue

            break

        threshold = int(message.content)

        await message.delete()
        db.guilds.update_one({"id": self.server_id}, {"$set": {"starboard.threshold": threshold}})

        embed = discord.Embed(
            title = "Do you want to set a logging channel?",
            description = "Would you like to set a logging channel for mod/admin actions?",
            color = 0x2F3136
        )

        await interaction.message.edit(embed=embed, view=LoggingSetupView(self.server_id))

    @discord.ui.button(label="No", style=discord.ButtonStyle.secondary)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        db.guilds.update_one({"id": self.server_id}, {"$set": {"starboard.enabled": False}})

        embed = discord.Embed(
            title = "Do you want to set a logging channel?",
            description = "Would you like to set a logging channel for mod/admin actions?",
            color = 0x2F3136
        )

        await interaction.response.edit_message(embed=embed, view=LoggingSetupView(self.server_id))

class LoggingSetupView(discord.ui.View):
    def __init__(self, server_id) -> None:
        super().__init__()
        self.server_id = server_id

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.primary)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.user != interaction.guild.owner:
            await interaction.response.send_message("You can't interact with this :D", ephemeral=True)
            return

        embed = discord.Embed(
            title="Mention the logging channel",
            description="Send a message containing the channel where logs should be sent",
            color=0x2F3136
        )

        await interaction.response.edit_message(embed=embed, view=None)

        while True:
            try:
                message = await interaction.client.wait_for("message", check=lambda m: m.author == interaction.user, timeout=30)
            except asyncio.TimeoutError:
                await interaction.followup.send("You took too long to respond.", ephemeral=True)
                return

            try:
                channel_id = int(message.content.replace("<#", "").replace(">", ""))
                channel = interaction.guild.get_channel(channel_id)

                if channel is None:
                    await interaction.followup.send("You must mention a channel.", ephemeral=True)
                    continue
                break
            except:
                await interaction.followup.send("You must mention a channel.", ephemeral=True)

        await message.delete()
        db.guilds.update_one({"id": self.server_id}, {"$set": {"log_channel": channel_id}})

        embed = discord.Embed(
            title="Setup complete!",
            description="We recommend you move the role 'Potato Bot' high up on the role list to make sure all features works properly",
            color=0x2F3136
        )

        await interaction.followup.send(embed=embed)

    @discord.ui.button(label="No", style=discord.ButtonStyle.secondary)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        embed = discord.Embed(
            title="Setup complete!",
            description="We recommend you move the role 'Potato Bot' high up on the role list to make sure all features works properly",
            color=0x2F3136
        )

        await interaction.response.edit_message(embed=embed)
