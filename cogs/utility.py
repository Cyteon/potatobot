# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon

import io

from asteval import Interpreter
aeval = Interpreter()

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
from deep_translator import GoogleTranslator

from utils import Checks

from PIL import ImageColor, Image

class Utility(commands.Cog, name="⚡ Utility"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_group(
        name="convert",
        description="Commands to convert stuff",
        usage="convert <subcommand>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def convert(self, context: Context) -> None:
        prefix = await self.bot.get_prefix(context)

        cmds = "\n".join([f"{prefix}convert {cmd.name} - {cmd.description}" for cmd in self.convert.walk_commands()])

        embed = discord.Embed(
            title=f"Help: Convert", description="List of available commands:", color=0xBEBEFE
        )
        embed.add_field(
            name="Commands", value=f"```{cmds}```", inline=False
        )

        await context.send(embed=embed)

    @convert.command(
        name="mb-gb",
        aliases=["mbgb", "mb-to-gb", "mb2gb"],
        description="Convert megabytes to gigabytes",
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    async def convert_mb_gb(self, context: Context, mb: float, binary: bool = True) -> None:
        if binary:
            gb = mb / 1024
        else:
            gb = mb / 1000

        await context.send(f"{mb}MB is equal to {gb}GB")

    @convert.command(
        name="gb-mb",
        aliases=["gbmb", "gb-to-mb", "gb2mb"],
        description="Convert gigabytes to megabytes",
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    async def convert_gb_mb(self, context: Context, gb: float, binary: bool = True) -> None:
        if binary:
            mb = gb * 1024
        else:
            mb = gb * 1000

        await context.send(f"{gb}GB is equal to {mb}MB")

    @convert.command(
        name="gb-tb",
        aliases=["gbtb", "gb-to-tb", "gb2tb"],
        description="Convert gigabytes to terabytes",
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    async def convert_gb_tb(self, context: Context, gb: float, binary: bool = True) -> None:
        if binary:
            tb = gb / 1024
        else:
            tb = gb / 1000

        await context.send(f"{gb}GB is equal to {tb}TB")

    @convert.command(
        name="tb-gb",
        aliases=["tbg", "tb-to-gb", "tb2gb"],
        description="Convert terabytes to gigabytes",
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    async def convert_tb_gb(self, context: Context, tb: float, binary: bool = True) -> None:
        if binary:
            gb = tb * 1024
        else:
            gb = tb * 1000

        await context.send(f"{tb}TB is equal to {gb}GB")

    @commands.hybrid_command(
        name="calc",
        description="Calculate a math expression.",
        aliases=["calculate"],
        usage="calc <expression>",
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def calc(self, context: Context, *, expression: str) -> None:
        try:
            result = aeval(expression)

            embed = discord.Embed(
                title="Calculator",
                description=f"**Input:**\n```{expression}```\n**Output:**\n```{result}```",
                color=0xBEBEFE
            )

            await context.send(embed=embed)
        except Exception as e:
            await context.send(f"An error occurred: {e}")

    @commands.hybrid_command(
        name="translate",
        description="Translate text to a specified language example: ,translate en hola",
        usage="translate <text> <language>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @app_commands.describe(text="The text you want to translate.")
    @app_commands.describe(language="The language you want to translate the text to.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def translate(self, context: Context, language, *, text: str) -> None:
        translated = GoogleTranslator(source='auto', target=language).translate(text)

        embed = discord.Embed(
            title="Translation",
            description=f"**Original text:**\n{text}\n\n**Translated text:**\n{translated}",
            color=0xBEBEFE,
        )
        embed.set_footer(text=f"Translated to {language}")
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="color",
        description="Get information about a color.",
        aliases=["colour"],
        usage="color <color>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def color(self, context: Context, color: str) -> None:
        try:
            rgb = ImageColor.getrgb(color)
            rgba = ImageColor.getcolor(color, "RGBA")
            grayscale = ImageColor.getcolor(color, "L")
            hex = hex_value = "#{:02x}{:02x}{:02x}".format(*rgb)


            embed = discord.Embed(
                title="Color Information",
                description="\n".join(
                    [
                        f"Color: **{color}**",
                        f"Hex: **{hex}**",
                        f"RGB: **RGB{rgb}**",
                        f"RGBA: **RGBA{rgba}**",
                        f"Grayscale: **{grayscale}**",
                    ]
                ),
                color=0xBEBEFE,
            )

            img = Image.new("RGB", (100, 100), rgb)

            with io.BytesIO() as image_binary:
                img.save(image_binary, "PNG")
                image_binary.seek(0)

                file = discord.File(fp=image_binary, filename="color.png")
                embed.set_image(url="attachment://color.png")

                await context.send(embed=embed, file=file)
        except ValueError:
            await context.send("Invalid color")
            return

async def setup(bot) -> None:
    await bot.add_cog(Utility(bot))
