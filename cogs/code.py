"""
The MIT License (MIT)

Copyright (c) 2022 Ogiroid Development Team

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
"""


import discord
import aiohttp
from discord import ui
from discord.ext import commands
from discord.ext.commands import Context

from utils import Checks


class Code(commands.Cog, name="💻 Code"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="code",
        description="Run code in any language, a modal will pop up",
        usage="code"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def code(self, context: Context) -> None:
        if context.interaction is None:
            await context.send("This command can only be used as a slash command.")
            return
        await context.interaction.response.send_modal(CodeModal())

class CodeModal(ui.Modal, title = "Run Code"):
    language = ui.TextInput(label = "Language", placeholder = "Enter the language of your code", style=discord.TextStyle.short, min_length = 1, max_length = 50)
    code = ui.TextInput(label = "Code", placeholder = "Enter your code here", style=discord.TextStyle.long, min_length = 1, max_length = 2000)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        async with aiohttp.ClientSession() as session:
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
            embed.add_field(name="Output", value=f"```\n{output}\n```" or "**<No output>**")

            await interaction.response.send_message(embed=embed)


async def setup(bot) -> None:
    await bot.add_cog(Code(bot))
