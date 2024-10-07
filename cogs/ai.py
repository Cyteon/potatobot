# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon

FILTER_LIST = ["@everyone", "@here", "<@&", "discord.gg", "discord.com/invite"]
WORD_BLACKLIST = ["nigger", "nigga", "n i g g e r"]

import discord
import requests
import os

import time
import asyncio
import functools
import http.client
import aiohttp
import base64
import aiohttp
import logging
import json

from io import BytesIO
from datetime import datetime

from better_profanity import profanity
from groq import Groq

from discord import app_commands, Webhook
from discord.ext import commands, tasks
from discord.ext.commands import Context
from utils import CONSTANTS, DBClient, Checks, CachedDB

from cryptography.fernet import Fernet

client = DBClient.client
db = client.potatobot

logger = logging.getLogger("discord_bot")

if not os.path.isfile(f"./config.json"):
    sys.exit("'config.json' not found! Please add it and try again.")
else:
    with open(f"./config.json") as file:
        config = json.load(file)

models = [
    "llama-3.2-90b-text-preview"
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
    "llama3-groq-70b-8192-tool-use-preview",
    "llama3-groq-8b-8192-tool-use-preview",
    "gemma2-9b-it"
]

api_key = os.getenv('FUSION_API_KEY')
secret_key = os.getenv('FUSION_SECRET_KEY')

ai_temp_disabled = False

ai_channels = []
c = db["ai_channels"]
data = c.find_one({ "listOfChannels": True })
logger.info("Initing AI channels")

if data:
    ai_channels = data["ai_channels"]
    logger.info("AI Channels data Found")
else:
    logger.info("Creating AI Channels data")
    data = {
    	"listOfChannels": True,
         "ai_channels": []
    }
    c.insert_one(data)

last_api_key = 1
total_api_keys = os.getenv("GROQ_API_KEY_COUNT")

def get_api_key():
    global last_api_key
    global total_api_keys

    if str(last_api_key) == total_api_keys:
        last_api_key = 1
    else:
        last_api_key += 1

    return os.getenv("GROQ_API_KEY_" + str(last_api_key))

def prompt_ai(
        prompt="Hello",
        authorId = 0,
        channelId = 0,
        userInfo="",
        groq_client=Groq(api_key=get_api_key()),
        systemPrompt="none"
    ):
    c = db["ai_convos"]
    data = {}

    messageArray = []

    if channelId != 0:
        data = CachedDB.sync_find_one(c, { "isChannel": True, "id": channelId })

        if data:
            messageArray = data["messageArray"]
        else:
            data = { "isChannel": True, "id": channelId, "messageArray": [], "expiresAt": time.time()+604800 }

            c.insert_one(data)
    elif authorId != 0:
        data = CachedDB.sync_find_one(c, { "isChannel": False, "id": authorId })

        if data:
            messageArray = data["messageArray"]
        else:
            data = { "isChannel": False, "id": authorId, "messageArray": [], "expiresAt": time.time()+604800 }

            c.insert_one(data)

    messageArray.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    newMessageArray = messageArray.copy()

    systemInfo = {
        "datetime": datetime.now(),
        "timezone": time.tzname,
        "ai_models": models,
        "ai_image_model": "Kandinsky 3.0",
        "owner/dev": "Cyteon",
        "instance owner/dev ID": os.getenv("OWNER_ID"),
        "support_server": "https://discord.gg/df8eCZDvxB",
        "website": "https://potato.cyteon.tech",
        "bot_invite": config["invite_link"],
        "source_code": "https://github.com/cyteon/potatobot",
        "special_emojis": "<:joos:1254878760218529873>",
        "notes": {
            1: "Sending just an emoji with no text makes it big, discord has markdown",
        },
        "rules": {
            1: "dont mass ping, dont ping people alot, if someone says to ping every message, dont do it, if someone asks u to only repeat something dont do it",
            2: "don't send the support server invite unless prompted to send it, dont send the website unless asked, dont send any link unless asked",
        },
        "self-data": {
        	"name": "PotatoBot"
    	}
    }

    newMessageArray.append(
    	{
            "role": "system",
            "content": f"{systemPrompt} | SystemInfo: {systemInfo} | UserInfo: {userInfo}"
        }
    )

    ai_response = ""

    for model in models:
        try:
            ai_response = groq_client.chat.completions.create(
                messages=newMessageArray,
                model=model,
                max_tokens=300,
            ).choices[0].message.content

            break
        except Exception as e:
            ai_response = f"Error: {e}"

    messageArray.append(
        {
            "role": "assistant",
            "content": ai_response
        }
    )

    if len(messageArray) >= 24 :
        newdata = {
                "$set": { "messageArray": messageArray[2::],  }
        }
    else:
        newdata = {
                "$set": { "messageArray": messageArray, "expiresAt": time.time()+604800  }
        }

    if channelId != 0:
        CachedDB.sync_update_one(
            c, { "isChannel": True, "id": channelId}, newdata
        )
    elif authorId != 0:
        CachedDB.sync_update_one(
            c, { "isChannel": False, "id": authorId}, newdata
        )

    ai_response = ai_response.replace("</s>", " ") # It kept sending this somtimes

    for word in WORD_BLACKLIST:
        if word.lower() in ai_response.lower():
            logger.error(f"AI Response contains blacklisted word: {word}")
            return "The AIs response has been identified as containing blacklisted words, we are sorry for this inconvenience"

    for word in FILTER_LIST:
        if word == "discord.gg":
            # TODO: Fix where if someone makes ai say support server invite and another invite it dosent get filtered
            if systemInfo["support_server"] in ai_response:
                continue
        ai_response =  ai_response.replace(word, "[FILTERED]")

    return ai_response

class Text2ImageAPI:
    def __init__(self, url):
        self.URL = url

    global AUTH_HEADERS
    AUTH_HEADERS = {
        'X-Key': f'Key {api_key}',
        'X-Secret': f'Secret {secret_key}',
    }

    def get_model(self):
        response = requests.get(self.URL + 'key/api/v1/models', headers=AUTH_HEADERS)
        data = response.json()
        return data[0]['id']

    def generate(self, prompt, model, images=1, width=1024, height=1024, style="DEFAULT", negative_prompt=""):
        params = {
            "type": "GENERATE",
            "stype": style,
            "numImages": images,
            "width": width,
            "height": height,
            "negativePromptUnclip": negative_prompt,
            "generateParams": {
                "query": f"{prompt}"
            }
        }
        data = {
            'model_id': (None, model),
            'params': (None, json.dumps(params), 'application/json')
        }
        response = requests.post(self.URL + 'key/api/v1/text2image/run', headers=AUTH_HEADERS, files=data)
        data = response.json()
        return data['uuid']

    def check_generation(self, request_id, attempts=10, delay=10):
        while attempts > 0:
            response = requests.get(self.URL + 'key/api/v1/text2image/status/' + request_id, headers=AUTH_HEADERS)
            data = response.json()

            logger.info(data)

            if data['status'] == 'DONE':
                return data['images']
            attempts -= 1
            time.sleep(delay)

        raise Exception("An error occured while generating the image")

class Ai(commands.Cog, name="🤖 AI"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.purge_conversations.start()
        self.ai_temp_disabled = False
        self.get_prefix = bot.get_prefix
        self.statsDB = bot.statsDB
        self.cooldown = commands.CooldownMapping.from_cooldown(5, 10, commands.BucketType.user)
        self.too_many_violations = commands.CooldownMapping.from_cooldown(3, 10, commands.BucketType.user)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author == self.bot or message.author.bot:
            return

        if not message.channel.id in ai_channels:
            return

        if message.content.startswith("-"):
            return

        if message.content.startswith(await self.bot.get_prefix(message)):
            return

        if self.ai_temp_disabled:
            await message.reply("AI is temporarily disabled due to techincal difficulties")
            return

        bucket = self.cooldown.get_bucket(message)
        retry_after = bucket.update_rate_limit()

        users_global = db["users_global"]

        user_data = await CachedDB.find_one(users_global, {"id": message.author.id})

        if not user_data:
            user_data = CONSTANTS.user_global_data_template(message.author.id)
            users_global.insert_one(user_data)

        if user_data:
            if user_data["ai_ignore"]:
                await message.reply("**You are being ignored by the AI, reason: " + user_data["ai_ignore_reason"] + "**")
                return

            if user_data["blacklisted"]:
                await message.reply("**You are blacklisted from using the bot, reason: " + user_data["blacklist_reason"] + "**")
                return

        if retry_after:
            embed = discord.Embed(
                title="Slow Down! Ratelimit hit",
                description=f"Try again <t:{(time.time() + int(retry_after)):.0f}:R>",
                color=discord.Color.red()
            )
            embed.set_footer(text="Further violations may result in a mute or blacklist.")

            await message.reply(embed=embed)

            bucket = self.too_many_violations.get_bucket(message)
            retry_after = bucket.update_rate_limit()

            if retry_after:
                embed = discord.Embed(
                    title="Too many violations! Max ratelimit hit",
                    description=f"You have been blacklisted from using the AI.",
                    color=discord.Color.red()
                )
                embed.set_footer(text=" If you believe this is a mistake, please contact the support server.")

                newdata = {
                    "$set": { "ai_ignore": True, "ai_ignore_reason": "Too many violations, max ratelimit hit."}
                }

                users_global.update_one(
                    { "id": message.author.id }, newdata
                )

                await message.reply(embed=embed)

            return

        if profanity.contains_profanity(message.content):
            newdata ={
                "$inc": { "inspect.nsfw_requests": 1}
            }

            users_global.update_one(
                { "id": message.author.id }, newdata
            )

        for word in WORD_BLACKLIST:
            if word.lower() in message.content.lower():
                newdata = {
                    "$inc": { "inspect.times_flagged": 1}
                }

                users_global.update_one(
                    { "id": message.author.id }, newdata
                )

                return await message.reply("Your message contains a blacklisted word, please refrain from using it.")

        if not "ai_requests" in user_data["inspect"]:
            newdata = {
                "$set": { "inspect.ai_requests": 0}
            }
            users_global.update_one(
                { "id": message.author.id }, newdata
            )

        if user_data["inspect"]["ai_requests"] == 0:
            embed = discord.Embed(
                description="By interacting with the ai in any way you agree to the following:\n- We will log: amount of ai requests, times you get flagged, nsfw request count\n- We will also store all messages you send to the AI in order to give the AI memory, these messages will be deleted after 7 days of inactivity and will not be seen by anyone other than the ai itself."
            )
            await message.reply(embed=embed)

        newdata ={
            "$inc": { "inspect.ai_requests": 1}
        }

        users_global.update_one(
            { "id": message.author.id }, newdata
        )

        c = db["guilds"]
        data = c.find_one({"id": message.guild.id})

        if not data:
            data = CONSTANTS.guild_data_template(message.guild.id)
            c.insert_one(data)

        if data["groq_api_key"] == "NONE":
            if not data["ai_access"]:
                await message.channel.send(f"**This server does not have access to built-in api keys, provide your own from https://console.groq.com/keys using {await self.bot.get_prefix(message)}groq-api-key <api_key>**")
                logger.info(f"{message.author} tried to ask AI in {message.guild.name} ({message.guild.id}): AI Disabled!")
                return
            client = Groq(api_key=get_api_key())
        else:
            cipher_suite = Fernet(os.getenv("HASHING_SECRET"))
            key = cipher_suite.decrypt(data["groq_api_key"]).decode()
            client = Groq(api_key=key)

        c = db["users"]
        userInfo = await CachedDB.find_one(c, {"id": message.author.id, "guild_id": message.guild.id})

        if not userInfo:
            userInfo = {}

        userInfo["user"] = message.author
        userInfo["channel"] = message.channel

        systemPrompt="You are a discord user, you are allowed to have opinions, also controversial ones, send a reply in max 500 characters. \n\nSystem info: {systemInfo} \n\nThe user's info:  {userInfo}"

        if "system_prompt" in data:
            if data["system_prompt"] != "NONE":
                systemPrompt = data["system_prompt"]

            if profanity.contains_profanity(systemPrompt):
                if hasattr(message.channel, "is_nsfw"):
                    if not message.channel.is_nsfw():
                        await message.reply("The system prompt contains profanity and this channel is not marked as NSFW. **Using default system prompt**")
                        systemPrompt = "NONE"

        loop = asyncio.get_running_loop()
        try:
            async with message.channel.typing():
                data = await loop.run_in_executor(None, functools.partial(prompt_ai, message.author.name + ": " + message.content, 0, message.channel.id, str(userInfo), groq_client=client, systemPrompt=systemPrompt))
                await message.reply(data)

                ai_requests = (self.statsDB.get("ai_requests") if self.statsDB.exists("ai_requests") else 0) + 1
                self.statsDB.set("ai_requests", ai_requests)
                self.statsDB.dump()

        except Exception as e:
            await message.reply("An error in the AI has occured")

        logger.info(f"AI replied to {message.author} in {message.guild.name} ({message.guild.id})")

    @tasks.loop(hours=1)
    async def purge_conversations(self):
        convos = db["ai_convos"]
        result = convos.delete_many({"expiresAt": {"$lt": time.time()}})

    @commands.cooldown(10, 60, commands.BucketType.default)
    @commands.hybrid_command(
        name="ai",
        description="Ask an AI for something",
        usage="ai <prompt>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def ai(self, context: Context, *, prompt: str) -> None:
        if self.ai_temp_disabled:
            await context.send("AI is temporarily disabled due to techincal difficulties")
            return

        await context.defer()

        users_global = db["users_global"]
        user_data = users_global.find_one({"id": context.author.id})

        if not user_data:
            user_data = CONSTANTS.user_global_data_template(context.author.id)
            users_global.insert_one(user_data)

        if user_data:
            if user_data["ai_ignore"]:
                await context.reply("**You are being ignored by the AI, reason: " + user_data["ai_ignore_reason"] + "**")
                return

        if profanity.contains_profanity(context.message.content):
            newdata ={
                "$inc": { "inspect.nsfw_requests": 1}
            }

            users_global.update_one(
                { "id": context.author.id }, newdata
            )

        if user_data["inspect"]["ai_requests"] == 0:
            embed = discord.Embed(
                description="By interacting with the ai in any way you agree to the following:\n- We will log: amount of ai requests, times you get flagged, nsfw request count\n- We will also store all messages you send to the AI in order to give the AI memory, these messages will be deleted after 7 days of inactivity and will not be seen by anyone other than the ai itself."
            )
            await context.send(embed=embed)

        if not "ai_requests" in user_data["inspect"]:
            newdata = {
                "$set": { "inspect.ai_requests": 0}
            }
            users_global.update_one(
                { "id": context.author.id }, newdata
            )

        newdata ={
            "$inc": { "inspect.ai_requests": 1}
        }

        users_global.update_one(
            { "id": context.author.id }, newdata
        )

        client = Groq(api_key=get_api_key())

        userInfo = { "user": context.author }

        c = db["users"]
        userData = c.find_one({"id": context.author.id, "guild_id": context.guild.id}) if context.guild else {}

        userInfo["data"] = userData

        loop = asyncio.get_running_loop()
        try:
            data = await loop.run_in_executor(None, functools.partial(prompt_ai, prompt, context.author.id, 0, str(userInfo), groq_client=client))

            await context.reply(data)

            ai_requests = (self.statsDB.get("ai_requests") if self.statsDB.exists("ai_requests") else 0) + 1
            self.statsDB.set("ai_requests", ai_requests)
            self.statsDB.dump()
        except Exception as e:
            await context.reply("An error in the AI has occured")

    @commands.hybrid_command(
        name="set-ai-channel",
        description="Set current channel as an AI channel",
        usage="set-ai-channel"
    )
    @commands.has_permissions(manage_channels=True)
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    async def set_ai_channel(self, context: Context):
        c = db["guilds"]
        data = c.find_one({"id": context.guild.id})

        if not data:
            data = CONSTANTS.guild_data_template(context.guild.id)
            c.insert_one(data)

        if data["groq_api_key"] == "NONE":
            if not data["ai_access"]:
                await context.send(f"**This server does not have access to built-in api keys, provide your own from https://console.groq.com/keys using {await self.bot.get_prefix(context)}groq-api-key <api_key>**")
                logger.info(f"{context.author} tried to set AI channel in {context.guild.name} ({context.guild.id}): AI Disabled!")
                return

            client = Groq(api_key=get_api_key())
        else:
            cipher_suite = Fernet(os.getenv("HASHING_SECRET"))
            key = cipher_suite.decrypt(data["groq_api_key"]).decode()
            client = Groq(api_key=key)

        await context.send("Setting channel...")

        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(None, functools.partial(prompt_ai, "Hello", groq_client=client))

        try:
             await context.channel.edit(slowmode_delay=5)
        except:
             pass

        await context.send(data)

        ai_channels.append(context.channel.id)

        c = db["ai_channels"]
        data = c.find_one({ "listOfChannels": True })

        newdata = {
                "$set": { "ai_channels": ai_channels }
        }

        c.update_one(
            { "listOfChannels": True }, newdata
        )

    @commands.hybrid_command(
        name="unset-ai-channel",
        description="Unset current channel as an AI channel",
        usage="unset-ai-channel"
    )
    @commands.has_permissions(manage_channels=True)
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    async def unset_ai_channel(self, context: Context):
        c = db["ai_channels"]

        ai_channels.remove(context.channel.id)

        await context.channel.edit(slowmode_delay=0)

        newdata = {
                "$set": { "ai_channels": ai_channels }
        }

        c.update_one(
            { "listOfChannels": True }, newdata
        )

        await context.send("Channel unset as AI channel")

    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.hybrid_command(
        name="create-ai-thread",
        description="Create AI thread so u dont have to do !ai",
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    async def create_ai_thread(self, context: Context, *, prompt = "Hello") -> None:
        c = db["guilds"]
        data = c.find_one({"id": context.guild.id})

        if not data:
            data = CONSTANTS.guild_data_template(context.guild.id)
            c.insert_one(data)

        if data["groq_api_key"] == "NONE":
            if not data["ai_access"]:
                await context.send(f"**This server does not have access to built-in api keys, provide your own from https://console.groq.com/keys using {await self.bot.get_prefix(context)}groq-api-key <api_key>**")
                logger.info(f"{context.author} tried to create AI thread in {context.guild.name} ({context.guild.id}): AI Disabled!")
                return

            client = Groq(api_key=get_api_key())
        else:
            cipher_suite = Fernet(os.getenv("HASHING_SECRET"))
            key = cipher_suite.decrypt(data["groq_api_key"]).decode()

            client = Groq(api_key=key)

        msg = await context.send("Creating, please wait")

        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(None, functools.partial(prompt_ai, prompt, groq_client=client))

        ai_requests = (self.statsDB.get("ai_requests") if self.statsDB.exists("ai_requests") else 0) + 1
        self.statsDB.set("ai_requests", ai_requests)
        self.statsDB.dump()

        newChannel = await context.channel.create_thread(
            name=f"AI Convo - {context.author}",
            type=discord.ChannelType.public_thread,
            slowmode_delay=5
        )

        await newChannel.send(data)
        await msg.delete()

        ai_channels.append(newChannel.id)

        c = db["ai_channels"]
        data = c.find_one({ "listOfChannels": True })

        newdata = {
                "$set": { "ai_channels": ai_channels }
        }

        c.update_one(
            { "listOfChannels": True }, newdata
        )

        await context.send("Thread created: " + newChannel.mention)

    @commands.hybrid_command(
        name="ai-image",
        description="Generate an ai image",
        usage="ai-image <prompt>",
        aliases=["image"]
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def ai_image(self, context: commands.Context, prompt: str) -> None:
        users_global = db["users_global"]
        user_data = users_global.find_one({"id": context.author.id})

        if not user_data:
            user_data = CONSTANTS.user_global_data_template(context.author.id)
            users_global.insert_one(user_data)

        if user_data:
            if user_data["ai_ignore"]:
                await context.reply("**You are being ignored by the AI, reason: " + user_data["ai_ignore_reason"] + "**")
                return

        if profanity.contains_profanity(prompt):
            newdata ={
                "$inc": { "inspect.nsfw_requests": 1}
            }

            users_global.update_one(
                { "id": context.author.id }, newdata
            )

            if hasattr(context.channel, "is_nsfw"):
                if not context.channel.is_nsfw():
                    return await context.send(f"NSFW requests are not allowed in non nsfw channels!", ephemeral=True)

        if not "ai_requests" in user_data["inspect"]:
            newdata = {
                "$set": { "inspect.ai_requests": 0}
            }
            users_global.update_one(
                { "id": context.author.id }, newdata
            )

        if user_data["inspect"]["ai_requests"] == 0:
            embed = discord.Embed(
                description="By interacting with the ai in any way you agree to the following:\n- We will log: amount of ai requests, times you get flagged, nsfw request count\n- We will also store all messages you send to the AI in order to give the AI memory, these messages will be deleted after 7 days of inactivity and will not be seen by anyone other than the ai itself."
            )
            await context.reply(embed=embed)

        newdata ={
            "$inc": { "inspect.ai_requests": 1}
        }

        users_global.update_one(
            { "id": context.author.id }, newdata
        )

        eta = int(time.time() + 20)

        msg = await context.send(f"Generating image... ETA: <t:{eta}:R>")

        attachments = []

        loop = asyncio.get_running_loop()
        try:
            data = await loop.run_in_executor(None, functools.partial(self.generate_image, context, prompt))
        except Exception as e:
            await msg.edit(content="An error occurred while generating the image")
            raise e

        logger.info(data)

        for image in data:
            attachments.append(discord.File(BytesIO(base64.b64decode(image)), "ai_image.png"))

        await msg.edit(content="Here you go!", attachments=attachments)

    @commands.hybrid_command(
        name="imagine",
        description="Generate an ai image, where you can change the model",
        usage="imagine <model (run command with no arguments for list)> <prompt>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def imagine(self, context: commands.Context, model: str = "none", *, prompt: str = "potato") -> None:
        options = {
            "chilloutmix": "emilianJR/chilloutmix_NiPrunedFp32Fix",
            "animagine": "cagliostrolab/animagine-xl-3.1",
            "nsfw-gen-v2": "UnfilteredAI/NSFW-gen-v2",
            "openjourney": "prompthero/openjourney-v4",
            "realistic-vision": "SG161222/Realistic_Vision_V4.0_noVAE",
            "ssd-1b": "segmind/SSD-1B",
            "dreamshaper": "Lykon/dreamshaper-xl-v2-turbo",
            "mobius": "Corcelio/mobius",
            "dalle": "ehristoforu/dalle-3-xl-v2",
            "sdxl": "stabilityai/stable-diffusion-xl-base-1.0",
        }

        nsfw_options = ["nsfw-gen-v2"]

        users_global = db["users_global"]
        user_data = users_global.find_one({"id": context.author.id})

        if not user_data:
            user_data = CONSTANTS.user_global_data_template(context.author.id)
            users_global.insert_one(user_data)

        if model not in options:
            return await context.send("Invalid model. Available models: " + ", ".join(options.keys()))

        if model in nsfw_options:
            if hasattr(context.channel, "is_nsfw"):
                if not context.channel.is_nsfw():
                    return await context.send(f"NSFW models are not allowed in non NSFW channels!", ephemeral=True)

        if user_data:
            if user_data["ai_ignore"]:
                await context.reply("**You are being ignored by the AI, reason: " + user_data["ai_ignore_reason"] + "**")
                return

        users_global = db["users_global"]

        user_data = users_global.find_one({"id": context.author.id})

        if not user_data:
            user_data = CONSTANTS.user_global_data_template(context.author.id)
            users_global.insert_one(user_data)

        if profanity.contains_profanity(prompt):
            newdata ={
                "$inc": { "inspect.nsfw_requests": 1}
            }

            users_global.update_one(
                { "id": context.author.id }, newdata
            )

            if hasattr(context.channel, "is_nsfw"):
                if not context.channel.is_nsfw():
                    return await context.send(f"NSFW requests are not allowed in non NSFW channels!", ephemeral=True)

        if not "ai_requests" in user_data["inspect"]:
            newdata = {
                "$set": { "inspect.ai_requests": 0}
            }
            users_global.update_one(
                { "id": context.author.id }, newdata
            )

        if user_data["inspect"]["ai_requests"] == 0:
            embed = discord.Embed(
                description="By interacting with the ai in any way you agree to the following:\n- We will log: amount of ai requests, times you get flagged, nsfw request count\n- We will also store all messages you send to the AI in order to give the AI memory, these messages will be deleted after 7 days of inactivity and will not be seen by anyone other than the ai itself."
            )
            await context.reply(embed=embed)
        newdata ={
            "$inc": { "inspect.ai_requests": 1}
        }

        users_global.update_one(
            { "id": context.author.id }, newdata
        )

        ETA = int(time.time() + 15)
        msg = await context.send(
            f"This might take a bit of time... ETA: <t:{ETA}:R>"
        )

        async with aiohttp.ClientSession() as session:
            api_key = os.getenv("HF_API_KEY")

            response = await session.post(
                "https://api-inference.huggingface.co/models/" + options[model],
                json={"inputs": prompt},
                headers={"Authorization": f"Bearer {api_key}"},
            )

            if response.status != 200:
                return await msg.edit(content="An error occurred while generating the image: " + http.client.responses[response.status])

            images = [discord.File(BytesIO(await response.read()), "ai_image.png")]

            await msg.edit(attachments=images, content="Here you go!")

    def generate_image(self, context: commands.Context, prompt: str, width=1024, height=1024, style="DEFAULT", negative_prompt="", number_of_images=1) -> None:
        api_key = os.environ.get('FUSION_API_KEY')
        secret_key = os.environ.get('FUSION_SECRET_KEY')

        if not api_key or not secret_key:
            context.send("API keys are missing. Please set the FUSION_API_KEY and FUSION_SECRET_KEY environment variables.")
            return

        api = Text2ImageAPI('https://api-key.fusionbrain.ai/')
        model_id = api.get_model()
        uuid = api.generate(prompt, model_id, images=number_of_images, width=width, height=height, style=style, negative_prompt=negative_prompt)
        images_data = api.check_generation(uuid)

        return images_data

    @commands.hybrid_command(
        name="system-prompt",
        description="Set the system prompt for the AI",
        usage="system-prompt <prompt>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @commands.has_permissions(manage_messages=True)
    async def system_prompt(self, context: Context, *, prompt: str = "") -> None:
        c = db["guilds"]
        data = c.find_one({"id": context.guild.id})

        if prompt == "":
            if data:
                if "system_prompt" in data:
                    return await context.send("Current system prompt: " + data["system_prompt"])
                else:
                    return await context.send("No system prompt set.")

        if profanity.contains_profanity(prompt):
            if not context.channel.is_nsfw():
                prompt = "NONE"
                await context.send("The system prompt contains profanity and this channel is not marked as NSFW. Please use an NSFW channel for NSFW prompts.")

        newdata = {
                "$set": { "system_prompt": prompt }
        }

        c.update_one(
            { "id": context.guild.id }, newdata
        )

        await context.send("System prompt set to: " + prompt)

    @commands.hybrid_command(
        name="reset-ai",
        description="Reset AI data",
        usage="reset-ai"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.check(Checks.command_not_disabled)
    @commands.has_permissions(manage_messages=True)
    async def reset_ai(self, context: Context) -> None:
        c = db["ai_convos"]
        c.delete_one({"id": context.channel.id})
        await context.send("AI data reset for " + context.channel.mention)

    @commands.command(
        name="toggle-ai",
        description="Reset AI data (owner only)",
    )
    @commands.is_owner()
    async def toggle_ai(self, context: Context) -> None:
        self.ai_temp_disabled = not self.ai_temp_disabled

        if self.ai_temp_disabled:
            await context.send("AI is now disabled globally")
        else:
            await context.send("AI is now enabled globally")

async def setup(bot) -> None:
    await bot.add_cog(Ai(bot))
