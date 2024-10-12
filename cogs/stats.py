# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon

import discord
import os
from discord.ext import commands
from discord.ext.commands import Context
from datetime import datetime

from easy_pil import Font

from PIL import Image, ImageDraw
import pickledb

from utils import Checks

db = pickledb.load('pickle/charts.db', False)

def textangle(draw, text, xy, angle, fill, font):
    img = Image.new('RGBA', font.getsize(text))
    d = ImageDraw.Draw(img)
    d.text((0, 0), text, font=font, fill=fill)
    w = img.rotate(angle, expand=1)
    draw.bitmap(xy, w, fill=fill)

class Stats(commands.Cog, name="📈 Stats"):
    def __init__(self, bot) -> None:
        self.bot = bot

    os.makedirs("graphs", exist_ok=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild == None:
            return

        if message.author == self.bot.user:
            return

        guild_id = str(message.guild.id)
        current_date = datetime.utcnow().date()

        if not db.exists(guild_id):
            db.set(guild_id, {})

        if str(current_date) not in db.get(guild_id):
            db.get(guild_id)[str(current_date)] = {"messages": 0}

        db.get(guild_id)[str(current_date)]["messages"] += 1

        current_users = message.guild.member_count

        db.get(guild_id)[str(current_date)]["users"] = current_users

        guild_data = db.get(guild_id)
        for date_str in list(guild_data.keys()):
            date = datetime.fromisoformat(date_str).date()
            if (current_date - date).days > 30:
                del guild_data[date_str]

        db.dump()

    @commands.hybrid_group(
        name="chart",
        description="Show chart of ... activity",
        usage="chart"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    async def chart(self, context: Context) -> None:
        subcommands = [cmd for cmd in self.chart.walk_commands()]

        data = []

        for subcommand in subcommands:
            description = subcommand.description.partition("\n")[0]
            data.append(f"{await self.bot.get_prefix(context)}chart {subcommand.name} - {description}")

        help_text = "\n".join(data)
        embed = discord.Embed(
            title=f"Help: Chart", description="List of available commands:", color=0xBEBEFE
        )
        embed.add_field(
            name="Commands", value=f"```{help_text}```", inline=False
        )

        await context.send(embed=embed)

    @chart.command(
        name="messages",
        description="Show chart of message activity",
        usage="chart messages"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    async def messages(self, context: Context) -> None:
        guild_id = str(context.guild.id)
        if not db.exists(guild_id):
            await context.send("No data available for this server.")
            return

        guild_data = db.get(guild_id)
        dates = sorted([datetime.fromisoformat(date_str).date() for date_str in guild_data.keys()])
        message_counts = [guild_data[str(date)]["messages"] for date in dates]

        total_messages = sum(message_counts)

        img = Image.new('RGB', (1600, 800), color=(32, 34, 38))
        draw = ImageDraw.Draw(img)
        font = Font.poppins(size=20)

        max_count = max(message_counts) if message_counts else 1
        max_count = max_count if max_count != 0 else 1  # Ensure max_count is never zero
        y_step = 100
        for y in range(100, 701, y_step):
            draw.line((100, y, 1500, y), fill=(64, 68, 75), width=2)
            number = (max_count - (y - 100) * max_count // 600) / 60 * 60
            number = int(str(number).split('.')[0])
            draw.text((20, y - 10), str(number), font=font, fill=(255, 255, 255))

        bar_color = (128, 128, 128)
        line_color = (0, 255, 255)
        previous_point = None

        for i in range(len(dates)):
            x = 200 + i * 40
            y = 700 - (message_counts[i] * 600 // max_count)
            draw.line((x, 700, x, y), fill=bar_color, width=20)
            if previous_point:
                draw.line((previous_point, (x, y)), fill=line_color, width=5)
            draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=line_color)
            previous_point = (x, y)
            textangle(draw, dates[i].strftime('%d %b'), (x - 40, 720), 45, (255, 255, 255), font)

        label_text = f'Messages - Last 30 days'
        total_text = f'Total Messages: {total_messages}'
        label_width, _ = draw.textsize(label_text, font=font)
        total_width, _ = draw.textsize(total_text, font=font)
        draw.text((20, 20), label_text, font=font, fill=(255, 255, 255))
        draw.text((1600 - total_width - 20, 20), total_text, font=font, fill=(255, 255, 255))

        img.save(f'graphs/graph-msgs-{context.channel.id}.png')
        await context.send(file=discord.File(f'graphs/graph-msgs-{context.channel.id}.png'))

        os.remove(f'graphs/graph-msgs-{context.channel.id}.png')

    @chart.command(
        name="members",
        description="Show chart of member count",
        usage="chart members"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    async def members(self, context: Context) -> None:
        guild_id = str(context.guild.id)
        if not db.exists(guild_id):
            await context.send("No data available for this server.")
            return

        guild_data = db.get(guild_id)
        dates = sorted([datetime.fromisoformat(date_str).date() for date_str in guild_data.keys()])
        user_counts = [((guild_data[str(date)]["users"]) if "users" in guild_data[str(date)] else 0) for date in dates]

        img = Image.new('RGB', (1600, 800), color=(32, 34, 38))
        draw = ImageDraw.Draw(img)
        font = Font.poppins(size=20)

        max_count = max(user_counts) if user_counts else 1
        max_count = max_count if max_count != 0 else 1

        y_step = 100

        for y in range(100, 701, y_step):
            draw.line((100, y, 1500, y), fill=(64, 68, 75), width=2)
            number = (max_count - (y - 100) * max_count // 600) / 60 * 60
            number = int(str(number).split('.')[0])
            draw.text((20, y - 10), str(number), font=font, fill=(255, 255, 255))

        bar_color = (128, 128, 128)
        line_color = (0, 255, 255)
        previous_point = None

        for i in range(len(dates)):
            x = 200 + i * 40
            y = 700 - (user_counts[i] * 600 // max_count)
            draw.line((x, 700, x, y), fill=bar_color, width=20)
            if previous_point:
                draw.line((previous_point, (x, y)), fill=line_color, width=5)
            draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=line_color)
            previous_point = (x, y)
            textangle(draw, dates[i].strftime('%d %b'), (x - 40, 720), 45, (255, 255, 255), font)

        label_text = f'Member Count - Last 30 days'

        label_width, _ = draw.textsize(label_text, font=font)
        draw.text((20, 20), label_text, font=font, fill=(255, 255, 255))

        img.save(f'graphs/graph-members-{context.channel.id}.png')
        await context.send(file=discord.File(f'graphs/graph-members-{context.channel.id}.png'))

        os.remove(f'graphs/graph-members-{context.channel.id}.png')

async def setup(bot) -> None:
    await bot.add_cog(Stats(bot))
