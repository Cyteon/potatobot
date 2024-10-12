import discord
import aiohttp
from discord import ui

class CodeModal(ui.Modal, title = "Run Code"):
    language = ui.TextInput(label = "Language", placeholder = "Enter the language of your code", style=discord.TextStyle.short, min_length = 1, max_length = 50)
    code = ui.TextInput(label = "Code", placeholder = "Enter your code here", style=discord.TextStyle.long, min_length = 1, max_length = 2000)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        async with aiohttp.ClientSession() as session:
            embed = discord.Embed(title=f"Running your {self.language.value} code...", color=0xFFFFFF)

            code = self.code.value[:1000].strip()
            shortened = len(code) > 1000
            lines = code.splitlines()
            shortened = shortened or (len(lines) > 40)
            code = "\n".join(lines[:40])
            code += shortened * "\n\n**Code shortened**"
            embed.add_field(name="Code", value=f"```{self.language.value}\n{code}```", inline=False)

            await interaction.response.send_message(embed=embed)

            response = await session.post(
                "https://emkc.org/api/v1/piston/execute",
                json={"language": self.language.value, "source": self.code.value},
            )

            json = await response.json()

            output = None
            try:
                output = json["output"]
            except KeyError:
                await interaction.response.send_message("An error occurred while running your code: \n\n" + json.get("message", "Unknown error"))
                return

            embed = discord.Embed(title=f"Ran your {json['language']} code", color=0xFFFFFF)
            output = output[:500].strip()
            shortened = len(output) > 500
            lines = output.splitlines()
            shortened = shortened or (len(lines) > 15)
            output = "\n".join(lines[:15])
            output += shortened * "\n\n**Output shortened**"
            embed.add_field(name="Output", value=f"```{self.language.value}\n{output}\n```" or "**<No output>**")

            await interaction.followup.send(embed=embed)
