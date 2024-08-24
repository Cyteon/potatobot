import discord

class JumpToMessageButton(discord.ui.Button):
    def __init__(self, message: discord.message) -> None:
        super().__init__(
            style=discord.ButtonStyle.link,
            label="Jump to message",
            url=f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        pass

class JumpToMessageView(discord.ui.View):
    def __init__(self, message: discord.message) -> None:
        super().__init__()
        self.add_item(JumpToMessageButton(message))
