# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon

import discord
import os
from datetime import datetime
from discord.ext import commands
from discord.ext.commands import Context

from utils import ServerLogger, DBClient, Checks
from ui.ticket import CreateButton, CloseButton, TrashButton

client = DBClient.client
db = client.potatobot

class Ticket(commands.Cog, name="🎫 Ticket"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="ticketembed",
        description="Command to make a embed for making tickets",
        usage="ticketembed"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @commands.has_permissions(administrator=True)
    async def ticketembed(self, context):
        await context.send(
            embed = discord.Embed(
                description="Press the button to create a new ticket!",
                color=discord.Color.blue()
            ),
            view = CreateButton()
        )

    @commands.hybrid_command(
        name="open",
        description="Open a ticket",
        usage="open"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    async def open(self, context: Context):
        c = db["guilds"]

        data = c.find_one({"id": context.guild.id})

        if not data:
            await context.send("**Tickets info not found! If you are an admin use `/setting` for more info**")
            return

        if not data["tickets_category"]:
            await context.send("**Tickets info not found! If you are an admin use `/setting` for more info**")
            return

        category: discord.CategoryChannel = discord.utils.get(context.guild.categories, id=data["tickets_category"])
        for ch in category.text_channels:
            if ch.topic == f"{context.author.id} DO NOT CHANGE THE TOPIC OF THIS CHANNEL!":
                await context.send("You already have a ticket in {0}".format(ch.mention))
                return
        r1 = None

        if data["tickets_support_role"]:
            r1 : discord.Role = context.guild.get_role(data["tickets_support_role"])
        else:
            r1 = context.guild.default_role
        overwrites = {
            context.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            r1: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True),
            context.author: discord.PermissionOverwrite(read_messages = True, send_messages=True),
            context.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        channel = await category.create_text_channel(
            name=str(context.author),
            topic=f"{context.author.id} DO NOT CHANGE THE TOPIC OF THIS CHANNEL!",
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

        await context.send(
            embed= discord.Embed(
                description = "Created your ticket in {0}".format(channel.mention),
                color = discord.Color.blurple()
            )
        )

        await ServerLogger.send_log(
            title="Ticket Created",
            description="Created by {0}".format(context.author.mention),
            color=discord.Color.green(),
            guild=context.guild,
            channel=context.channel
        )

    @commands.hybrid_group(
        name="ticket",
        description="Commands to manage a ticket",
        usage="ticket"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    async def ticket(self, context: Context):
        subcommands = [cmd for cmd in self.ticket.walk_commands()]

        data = []

        for subcommand in subcommands:
            description = subcommand.description.partition("\n")[0]
            data.append(f"{await self.bot.get_prefix(context)}ticket {subcommand.name} - {description}")

        help_text = "\n".join(data)
        embed = discord.Embed(
            title=f"Help: Ticket", description="List of available commands:", color=0xBEBEFE
        )
        embed.add_field(
            name="Commands", value=f"```{help_text}```", inline=False
        )

        await context.send(embed=embed)

    @ticket.command(
        name="upgrade",
        description="Remove support role access from the ticket",
        usage="ticket upgrade"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @commands.has_permissions(manage_channels=True)
    async def upgrade(self, context: Context):
        try:
            int(context.channel.topic.split()[0])
        except:
            return await context.send("This is not a ticket channel.")

        c = db["guilds"]
        guild = c.find_one({"id": context.guild.id})

        if not guild or not guild.get("tickets_support_role"):
            return await context.send("Support role not configured for this server.")

        support_role = context.guild.get_role(guild["tickets_support_role"])
        if not support_role:
            return await context.send("Support role not found.")

        if support_role not in context.channel.overwrites:
            return await context.send("This ticket is already upgraded.")

        await context.channel.set_permissions(support_role, overwrite=None)
        await context.send("Support role access has been removed from this ticket.")

        await ServerLogger.send_log(
            title="Ticket Upgraded",
            description=f"{context.author.mention} upgraded ticket {context.channel.name}",
            color=discord.Color.purple(),
            guild=context.guild,
            channel=context.channel
        )

    @ticket.command(name="downgrade", description="Restore support role access to the ticket", usage="ticket downgrade")
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @commands.has_permissions(manage_channels=True)
    async def downgrade(self, context: Context):
        try:
            int(context.channel.topic.split()[0])
        except:
            return await context.send("This is not a ticket channel.")

        c = db["guilds"]
        guild = c.find_one({"id": context.guild.id})

        if not guild or not guild.get("tickets_support_role"):
            return await context.send("Support role not configured for this server.")

        support_role = context.guild.get_role(guild["tickets_support_role"])
        if not support_role:
            return await context.send("Support role not found.")

        if support_role in context.channel.overwrites:
            return await context.send("This ticket is already accessible to the support role.")

        await context.channel.set_permissions(support_role, read_messages=True, send_messages=True)
        await context.send("Support role access has been restored to this ticket.")

        await ServerLogger.send_log(
            title="Ticket Downgraded",
            description=f"{context.author.mention} downgraded ticket {context.channel.name}",
            color=discord.Color.green(),
            guild=context.guild,
            channel=context.channel
        )

    @ticket.command(
        name="add",
        description="Add a user to the ticket",
        usage="ticket add <user>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    async def add(self, context: Context, user: discord.Member):
        try:
            int(context.channel.topic.split()[0])
        except:
            return await context.send("This is not a ticket channel.")

        member = context.guild.get_member(int(context.channel.topic.split(" ")[0]))

        if not context.author == member and not context.author.guild_permissions.manage_channels:
            return await context.send("You don't have permission to add users to this ticket.")

        if user in context.channel.members:
            return await context.send(f"{user.mention} is already in this ticket.")

        await context.channel.set_permissions(user, read_messages=True, send_messages=True)
        await context.send(f"Added {user.mention} to the ticket.")

        await ServerLogger.send_log(
            title="User Added to Ticket",
            description=f"{context.author.mention} added {user.mention} to ticket {context.channel.name}",
            color=discord.Color.blue(),
            guild=context.guild,
            channel=context.channel
        )

    @ticket.command(
        name="remove",
        description="Remove a user from the ticket",
        usage="ticket remove <user>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    async def remove(self, context: Context, user: discord.Member):
        try:
            int(context.channel.topic.split()[0])
        except:
            return await context.send("This is not a ticket channel.")

        member = context.guild.get_member(int(context.channel.topic.split(" ")[0]))

        if not context.author == member and not context.author.guild_permissions.manage_channels:
            return await context.send("You don't have permission to remove users from this ticket.")

        if user not in context.channel.members:
            return await context.send(f"{user.mention} is not in this ticket.")

        if user == context.channel.guild.get_member(int(context.channel.topic.split(" ")[0])):
            return await context.send("You can't remove the ticket creator.")

        await context.channel.set_permissions(user, overwrite=None)
        await context.send(f"Removed {user.mention} from the ticket.")

        await ServerLogger.send_log(
            title="User Removed from Ticket",
            description=f"{context.author.mention} removed {user.mention} from ticket {context.channel.name}",
            color=discord.Color.orange(),
            guild=context.guild,
            channel=context.channel
        )

    @ticket.command(
        name="claim",
        description="Claim the ticket",
        usage="ticket claim"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    async def claim(self, context: Context):
        try:
            int(context.channel.topic.split()[0])
        except:
            return await context.send("This is not a ticket channel.")

        member = context.guild.get_member(int(context.channel.topic.split(" ")[0]))

        if context.author == member:
            return await context.send("This is your ticket.")

        guilds = db["guilds"]
        guild = guilds.find_one({"id": context.guild.id})

        if guild and guild.get("tickets_support_role"):
            support_role = context.guild.get_role(guild["tickets_support_role"])

            await context.channel.set_permissions(member, overwrite=None)
            await context.channel.set_permissions(support_role, read_messages=True, send_messages=False)
            await context.channel.set_permissions(context.author, read_messages=True, send_messages=True)

            embed = discord.Embed(
                title="Ticket Claimed",
                description=f"{context.author.mention} will now handle this ticket.",
            )

            await context.send(embed=embed)

            await ServerLogger.send_log(
                title="Ticket Claimed",
                description=f"{context.author.mention} claimed ticket {context.channel.name}",
                color=discord.Color.green(),
                guild=context.guild,
                channel=context.channel
            )

    @ticket.command(
        name="unclaim",
        description="Unclaim the ticket",
        usage="ticket unclaim"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    async def unclaim(self, context: Context):
        try:
            int(context.channel.topic.split()[0])
        except:
            return await context.send("This is not a ticket channel.")

        member = context.guild.get_member(int(context.channel.topic.split(" ")[0]))

        if context.author == member:
            return await context.send("This is your ticket.")

        guilds = db["guilds"]
        guild = guilds.find_one({"id": context.guild.id})

        if guild and guild.get("tickets_support_role"):
            support_role = context.guild.get_role(guild["tickets_support_role"])

            await context.channel.set_permissions(member, read_messages=True, send_messages=True)
            await context.channel.set_permissions(support_role, read_messages=True, send_messages=True)
            await context.channel.set_permissions(context.author, overwrite=None)

            embed = discord.Embed(
                title="Ticket Unclaimed",
                description=f"{context.author.mention} has unclaimed this ticket.",
            )

            await context.send(embed=embed)


    @ticket.command(
        name="close",
        description="Close the ticket",
        usage="ticket close"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    async def close(self, context: Context):
        try:
            int(context.channel.topic.split()[0])
        except:
            return await context.send("This is not a ticket channel.")

        member = context.guild.get_member(int(context.channel.topic.split(" ")[0]))

        if not context.author == member and not context.author.guild_permissions.manage_channels:
            return await context.send("You don't have permission to close this ticket.")

        await context.send("Starting ticket closing, dont run command again")

        os.makedirs("logs", exist_ok=True)
        log_file = f"logs/{context.channel.id}.log"
        with open(log_file, "w", encoding="UTF-8") as f:
            f.write(
                f'Ticket log from: #{context.channel} ({context.channel.id}) in the guild "{context.guild}" ({context.guild.id}) at {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}\n'
            )
            async for message in context.channel.history(
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
        data = guilds.find_one({"id": context.guild.id})

        if data["log_channel"]:
            log_channel = context.guild.get_channel(data["log_channel"])

            if log_channel:
                try:
                    await log_channel.send(file=discord.File(log_file))

                    embed = discord.Embed(
                        title="Ticket Closed",
                        description=f"Ticket {context.channel.name} closed by {context.author.mention}",
                        color=discord.Color.orange()
                    )

                    await log_channel.send(embed=embed)
                except Exception as e:
                    return await context.send("An error occurred, " + str(e))

        try:
            with open (log_file, "rb") as f:
                await member.send(f"Your ticket in {context.guild} has been closed. Transcript: ", file=discord.File(f))
        except Exception as e:
            await context.channel.send(
                f"Couldn't send the log file to {member.mention}, " + str(e)
            )

        await context.channel.set_permissions(member, overwrite=None)
        await context.channel.edit(name=f"closed-{context.channel.name}")

        os.remove(log_file)

        await context.channel.send(
            embed= discord.Embed(
                description="Ticket Closed!",
                color = discord.Color.red()
            ),
            view = TrashButton()
        )

    @ticket.command(
        name="delete",
        description="Delete the ticket",
        usage="ticket delete"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)

    @commands.has_permissions(manage_channels=True)
    async def delete(self, context: Context):
        if not context.channel.name.startswith("closed-"):
            return await context.send("Please close the ticket first")

        await context.channel.delete()

        await ServerLogger.send_log(
            title="Ticket Deleted",
            description=f"{context.author.mention} deleted ticket {context.channel.name}",
            color=discord.Color.red(),
            guild=context.guild,
            channel=context.channel
        )

async def setup(bot) -> None:
    await bot.add_cog(Ticket(bot))
    bot.add_view(CreateButton())
    bot.add_view(CloseButton())
    bot.add_view(TrashButton())
