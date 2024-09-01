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

from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

from utils import Checks
from ui.code import CodeModal

class Code(commands.Cog, name="💻 Code"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="code",
        description="Run code in (almost) any language, a modal will pop up",
        usage="code"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def code(self, context: Context) -> None:
        if not context.interaction:
            await context.send("This command can only be used as a slash command.")
            return
        await context.interaction.response.send_modal(CodeModal())

async def setup(bot) -> None:
    await bot.add_cog(Code(bot))
