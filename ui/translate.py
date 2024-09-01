import discord
import aiohttp
from discord import ui

from deep_translator import GoogleTranslator

class TranslateModal(ui.Modal, title = "Translate"):
    def __init__(self, message: discord.Message):
        super().__init__(timeout = 60)
        self.message = message

    language = ui.TextInput(label = "Language", placeholder = "Enter the language to translate this message to", style=discord.TextStyle.short, min_length = 1, max_length = 50)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            translated = GoogleTranslator(source='auto', target=self.language.value.lower()).translate(self.message.content)

            embed = discord.Embed(title = "Translation", description = translated, color = discord.Color.blurple())
            embed.set_footer(text = f"Original: \"{self.message.content}\"")

            await interaction.response.send_message(embed = embed, ephemeral = True)
        except:
            await interaction.response.send_message(content = "Failed to translate message", ephemeral = True)
