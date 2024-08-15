import discord
import asyncio
import os
from datetime import datetime

from discord.ui import Button, button, View

from utils import ServerLogger, DBClient

db = DBClient.db

class CreateButton(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Create Ticket",style=discord.ButtonStyle.blurple, emoji="🎫",custom_id="ticketopen")
    async def ticket(self, interaction: discord.Interaction, button: Button):
        c = db["guilds"]

        data = c.find_one({"id": interaction.guild.id})

        if not data:
            await interaction.channel.send("**Tickets info not found! If you are an admin use `/setting` for more info**")
            return

        if not data["tickets_category"] or not data["tickets_support_role"]:
            await interaction.channel.send("**Tickets info not found! If you are an admin use `/setting` for more info**")
            return


        await interaction.response.defer(ephemeral=True)
        category: discord.CategoryChannel = discord.utils.get(interaction.guild.categories, id=data["tickets_category"])
        for ch in category.text_channels:
            if ch.topic == f"{interaction.user.id} DO NOT CHANGE THE TOPIC OF THIS CHANNEL!":
                await interaction.followup.send("You already have a ticket in {0}".format(ch.mention), ephemeral=True)
                return

        r1 : discord.Role = interaction.guild.get_role(data["tickets_support_role"])
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            r1: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True),
            interaction.user: discord.PermissionOverwrite(read_messages = True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        channel = await category.create_text_channel(
            name=str(interaction.user),
            topic=f"{interaction.user.id} DO NOT CHANGE THE TOPIC OF THIS CHANNEL!",
            overwrites=overwrites
        )
        await channel.send("{0} a ticket has been created!".format(r1.mention))
        await channel.send(
            embed=discord.Embed(
                title=f"Ticket Created!",
                description="Don't ping a staff member, they will be here soon.",
                color = discord.Color.green()
            ),
            view = CloseButton()
        )
        await channel.send("Please describe your issue")

        await interaction.followup.send(
            embed= discord.Embed(
                description = "Created your ticket in {0}".format(channel.mention),
                color = discord.Color.blurple()
            ),
            ephemeral=True
        )

        await ServerLogger.send_log(
            title="Ticekt Created",
            description="Created by {0}".format(interaction.user.mention),
            color=discord.Color.green(),
            guild=interaction.guild,
            channel=interaction.channel
        )


class CloseButton(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Close the ticket",style=discord.ButtonStyle.red,custom_id="closeticket",emoji="🔒")
    async def close(self, interaction: discord.Interaction, button: Button):
        c = db["guilds"]

        data = c.find_one({"id": interaction.guild.id})

        if not data:
            await interaction.channel.send("**Tickets info not found! If you are an admin use `/setting` for more info**")
            return

        if not data["tickets_category"] or not data["tickets_support_role"]:
            await interaction.channel.send("**Tickets info not found! If you are an admin use `/setting` for more info**")
            return

        await interaction.response.defer(ephemeral=True)

        await interaction.channel.send("Closing this ticket in 3 seconds!")

        await asyncio.sleep(3)

        category: discord.CategoryChannel = discord.utils.get(interaction.guild.categories, id = data["tickets_category"])
        r1 : discord.Role = interaction.guild.get_role(data["tickets_support_role"])
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            r1: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        await interaction.channel.edit(category=category, overwrites=overwrites)
        await interaction.channel.send(
            embed= discord.Embed(
                description="Ticket Closed!",
                color = discord.Color.red()
            ),
            view = TrashButton()
        )

        member = interaction.guild.get_member(int(interaction.channel.topic.split(" ")[0]))

        os.makedirs("logs", exist_ok=True)
        log_file = f"logs/{interaction.channel.id}.log"
        with open(log_file, "w", encoding="UTF-8") as f:
            f.write(
                f'Ticket log from: #{interaction.channel} ({interaction.channel.id}) in the guild "{interaction.guild}" ({interaction.guild.id}) at {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}\n'
            )
            async for message in interaction.channel.history(
                limit=None, oldest_first=True
            ):
                attachments = []
                for attachment in message.attachments:
                    attachments.append(attachment.url)
                attachments_text = (
                    f"[Attached File{'s' if len(attachments) >= 2 else ''}: {', '.join(attachments)}]"
                    if len(attachments) >= 1
                    else ""
                )
                f.write(
                    f"{message.created_at.strftime('%d.%m.%Y %H:%M:%S')} {message.author} {message.id}: {message.clean_content} {attachments_text}\n"
                )

        guilds = DBClient.client.potatobot["guilds"]
        data = guilds.find_one({"id": interaction.guild.id})

        if data["log_channel"]:
            log_channel = interaction.guild.get_channel(data["log_channel"])

            if log_channel:
                try:
                    await log_channel.send(file=discord.File(log_file))

                    embed = discord.Embed(
                        title="Ticket Closed",
                        description=f"Ticket {interaction.channel.name} closed by {interaction.user.mention}",
                        color=discord.Color.orange()
                    )

                    await log_channel.send(embed=embed)
                except:
                    pass

        try:
            with open (log_file, "rb") as f:
                await member.send(f"Your ticket in {interaction.guild} has been closed. Transcript: ", file=discord.File(f))
        except Exception as e:
            await interaction.channel.send(
                f"Couldn't send the log file to {member.mention}, " + str(e)
            )

        os.remove(log_file)


class TrashButton(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Delete the ticket", style=discord.ButtonStyle.red, emoji="🚮", custom_id="trash")
    async def trash(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        await interaction.channel.send("Deleting the ticket in 3 seconds")
        await asyncio.sleep(3)

        await interaction.channel.delete()
        await ServerLogger.send_log(
            title="Ticket Deleted",
            description=f"Deleted by {interaction.user.mention}, ticket: {interaction.channel.name}",
            color=discord.Color.red(),
            guild=interaction.guild,
            channel=interaction.channel
        )
