import discord

class deleteconfirm(discord.ui.View):
    def __init__(self, user, channel):
        super().__init__(timeout=None)
        self.user = user
        self.channel = channel

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.red)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            return

        old_channel = self.channel

        await self.channel.delete()

        new_channel = await old_channel.clone()

        await new_channel.edit(position=old_channel.position)

        await new_channel.send("Channel has been recreated")

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.green)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()
