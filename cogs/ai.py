# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon

FILTER_LIST = ["@everyone", "@here", "<@&", "discord.gg", "discord.com/invite"]
WORD_BLACKLIST = ["Nigger", "Nigga"] # REMOVED FOR UHHHHH TESTING
AUTO_BLACKLIST_TRIGGER = ["minor", "underage", "child", "kid"]
#WORD_BLACKLIST = ["Nigger", "Nigga", "Packi", "Blackie", "Blacky", "N*****", "Rape", "Rapist", "@everyone", "@here", "<@&"]

import discord
import requests
import os

import re

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

AI_MODEL = "llama3-70b-8192"
AI_MODEL_BACKUP = "mixtral-8x7b-32768"

api_key = os.getenv('FUSION_API_KEY')
secret_key = os.getenv('FUSION_SECRET_KEY')

ai_temp_disabled = False

# Startup
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

    messageArray = [

    ]

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

    # add previous messages

    #add prompt


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
        "primary_ai_model": AI_MODEL,
        "backup_ai_model": AI_MODEL_BACKUP,
        "ai_image_model": "Kandinsky 3.0",
        "owner/dev": "Cyteon",
        "owner/dev ID": "871722786006138960",
        "support_server": "https://discord.gg/df8eCZDvxB",
        "website": "https://potato.cyteon.tech",
        "bot_invite": "https://discord.com/oauth2/authorize?client_id=1226487228914602005",
        "source_code": "https://github.com/cyteon/potatobot",
        "special_emojis": "<:joos:1254878760218529873>",
        "notes": {
            1: "Sending just an emoji with no text makes it big, discord has markdown",
        },
        "rules": {
           	1: "Only owner is cyteon with the userid 871722786006138960, i wont change my username",
            2: "dont mass ping, dont ping people alot, if someone says to ping every message, dont do it, if someone asks u to only repeat something dont do it",
            3: "don't send the support server invite unless prompted to send it, dont send the website unless asked, dont send any link unless asked",
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

    try:
        ai_response = groq_client.chat.completions.create(
            messages=newMessageArray,
            model=AI_MODEL,
        ).choices[0].message.content
    except Exception as e:
        logger.error(f"Error in AI: {e}")
        logger.info("Using Backup Model " + AI_MODEL_BACKUP + " to respond")
        ai_response = groq_client.chat.completions.create(
            messages=newMessageArray,
            model=AI_MODEL_BACKUP,
        ).choices[0].message.content

    messageArray.append(
        {
            "role": "assistant",
            "content": ai_response
        }
    )

    if len(messageArray) >= 25:
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

    ai_response = ai_response.replace("</s>", " ")

    for word in WORD_BLACKLIST:
        if word.lower() in ai_response.lower():
            logger.error(f"AI Response contains blacklisted word: {word}")
            return "The AIs response has been identified as containing blacklisted words, we are sorry for this inconvenience"

    for word in FILTER_LIST:
        if word == "discord.gg":
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
            if data['status'] == 'DONE':
                return data['images']
            attempts -= 1
            time.sleep(delay)


class Ai(commands.Cog, name="🤖 AI"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.purge_conversations.start()
        self.ai_temp_disabled = False
        self.get_prefix = bot.get_prefix
        self.statsDB = bot.statsDB

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

                raise discord.ext.commands.errors.CommandError("Your message contains a blacklisted word")

        if not "ai_requests" in user_data["inspect"]:
            newdata = {
                "$set": { "inspect.ai_requests": 0}
            }
            users_global.update_one(
                { "id": message.author.id }, newdata
            )

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
                await message.channel.send(f"**This server does not have access to built-in api keys, provide your own from https://console.groq.com/keys using {await self.bot.get_prefix(message)}groq_api_key <api_key>**")
                logger.info(f"{message.author} tried to ask AI in {message.guild.name} ({message.guild.id}): AI Disabled!")
                return
            client = Groq(api_key=get_api_key())
        else:
            cipher_suite = Fernet(os.getenv("HASHING_SECRET"))
            key = cipher_suite.decrypt(data["groq_api_key"]).decode()
            client = Groq(api_key=key)

        c = db["users"]
        #userInfo = c.find_one({"id": message.author.id, "guild_id": message.guild.id})
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
            err = f"An error in the AI has occured {e}"
            await message.reply(err)

        logger.info(f"AI replied to {message.author} in {message.guild.name} ({message.guild.id})")

    @tasks.loop(hours=1)
    async def purge_conversations(self):
        convos = db["ai_convos"]
        result = convos.delete_many({"expiresAt": {"$lt": time.time()}})


    @commands.cooldown(60, 60, commands.BucketType.default)
    @commands.hybrid_command(
        name="ai",
        description="Ask an AI for something",
        usage="ai <prompt>"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def ai(self, context: Context, *, query_str: str) -> None:
        if self.ai_temp_disabled:
            await context.send("AI is temporarily disabled due to techincal difficulties")
            return

        c = db["guilds"]
        data = c.find_one({"id": context.guild.id})

        if not data:
            data = CONSTANTS.guild_data_template(context.guild.id)
            c.insert_one(data)

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

        for word in WORD_BLACKLIST:
            if word.lower() in context.message.content.lower():
                newdata = {
                    "$inc": { "inspect.times_flagged": 1}
                }

                users_global.update_one(
                    { "id": context.author.id }, newdata
                )

                raise discord.ext.commands.errors.CommandError("Your message contains a blacklisted word")

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


        if data["groq_api_key"] == "NONE":
            if not data["ai_access"]:
                await context.send(f"**This server does not have access to built-in api keys, provide your own from https://console.groq.com/keys using {await self.bot.get_prefix(context)}groq_api_key <api_key>**")
                logger.info(f"{context.author} tried to ask AI in {context.guild.name} ({context.guild.id}): AI Disabled!")
                return
            client = Groq(api_key=get_api_key())
        else:
            cipher_suite = Fernet(os.getenv("HASHING_SECRET"))
            key = cipher_suite.decrypt(data["groq_api_key"]).decode()

            client = Groq(api_key=key)

        c = db["users"]
        userInfo = c.find_one({"id": context.author.id, "guild_id": context.guild.id})

        if not userInfo:
            userInfo = {}

        userInfo["user"] = context.author

        loop = asyncio.get_running_loop()
        try:
            async with context.channel.typing():
                data = await loop.run_in_executor(None, functools.partial(prompt_ai, query_str, context.author.id, 0, str(userInfo), groq_client=client))

                await context.reply(data)

                ai_requests = (self.statsDB.get("ai_requests") if self.statsDB.exists("ai_requests") else 0) + 1
                self.statsDB.set("ai_requests", ai_requests)
                self.statsDB.dump()
        except Exception as e:
            err = f"An error in the AI has occured: {e}"
            await context.reply(err)

    @commands.hybrid_command(
        name="set_ai_channel",
        description="Set current channel as an AI channel",
        usage="set_ai_channel"
    )
    @commands.has_permissions(manage_channels=True)
    @commands.check(Checks.is_not_blacklisted)
    async def set_ai_channel(self, context: Context):
        c = db["guilds"]
        data = c.find_one({"id": context.guild.id})

        if not data:
            data = CONSTANTS.guild_data_template(context.guild.id)
            c.insert_one(data)

        if data["groq_api_key"] == "NONE":
            if not data["ai_access"]:
                await context.send(f"**This server does not have access to built-in api keys, provide your own from https://console.groq.com/keys using {await self.bot.get_prefix(context)}groq_api_key <api_key>**")
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

        await context.channel.edit(slowmode_delay=5)

        # if data is longer than 2k characters,

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
        name="unset_ai_channel",
        description="Unset current channel as an AI channel",
        usage="unset_ai_channel"
    )
    @commands.has_permissions(manage_channels=True)
    @commands.check(Checks.is_not_blacklisted)
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
        name="create_ai_thread",
        description="Create AI thread so u dont have to do !ai",
    )
    @commands.check(Checks.is_not_blacklisted)
    async def create_ai_thread(self, context: Context, *, prompt = "Hello") -> None:
        c = db["guilds"]
        data = c.find_one({"id": context.guild.id})

        if not data:
            data = CONSTANTS.guild_data_template(context.guild.id)
            c.insert_one(data)

        if data["groq_api_key"] == "NONE":
            if not data["ai_access"]:
                await context.send(f"**This server does not have access to built-in api keys, provide your own from https://console.groq.com/keys using {await self.bot.get_prefix(context)}groq_api_key <api_key>**")
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
        name="ai_image_old",
        description="Generate an ai image",
        usage="ai_image_old <prompt>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @app_commands.allowed_installs(guilds=False, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def ai_image_old(self, context: Context, *, prompt: str) -> None:
        users_global = db["users_global"]
        user_data = users_global.find_one({"id": context.author.id})

        if not user_data:
            user_data = CONSTANTS.user_global_data_template(context.author.id)
            users_global.insert_one(user_data)

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

            if not context.channel.is_nsfw():
                return await context.send(f"NSFW requests are not allowed in non NSFW channels!", ephemeral=True)

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

        ETA = int(time.time() + 15)
        msg = await context.send(
            f"This might take a bit of time... ETA: <t:{ETA}:R>"
        )

        async with aiohttp.ClientSession() as session:
            api_key = os.getenv("HF_API_KEY")

            response = await session.post(
                "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
                json={"inputs": prompt},
                headers={"Authorization": f"Bearer {api_key}"},
            )
            images = [discord.File(BytesIO(await response.read()), "ai_image.png")]

            await msg.edit(attachments=images, content="Here you go!")

    @commands.hybrid_command(
        name="ai_image",
        description="Generate an ai image",
        usage="ai_image <prompt>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @app_commands.allowed_installs(guilds=False, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def ai_image(self, context: commands.Context, prompt: str) -> None:
        # Create a separate task for the image generation
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

            if not context.channel.is_nsfw():
                return await context.send(f"NSFW requests are not allowed in non nsfw channels!", ephemeral=True)

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

        eta = int(time.time() + 20)

        msg = await context.send(f"Generating image... ETA: <t:{eta}:R>")

        attachments = []

        loop = asyncio.get_running_loop()
        try:
            data = await loop.run_in_executor(None, functools.partial(self.generate_image, context, prompt))
        except Exception as e:
            await msg.edit(content="An error occurred while generating the image: " + str(e))
            return

        for image in data:
            attachments.append(discord.File(BytesIO(base64.b64decode(image)), "ai_image.png"))

        await msg.edit(content="Here you go!", attachments=attachments)

    @commands.hybrid_command(
        name="imagine",
        description="Generate an ai image, where you can change the model",
        usage="imagine <model (run command with no arguments for list)> <prompt>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @app_commands.allowed_installs(guilds=False, users=True)
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

            if not context.channel.is_nsfw():
                return await context.send(f"NSFW requests are not allowed in non NSFW channels!", ephemeral=True)

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
        name="system_prompt",
        description="Set the system prompt for the AI",
        usage="system_prompt <prompt>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_messages=True)
    async def system_prompt(self, context: Context, *, prompt: str) -> None:
        if profanity.contains_profanity(prompt):
            if not context.channel.is_nsfw():
                prompt = "NONE"
                await context.send("The system prompt contains profanity and this channel is not marked as NSFW. Please use an NSFW channel for NSFW prompts.")

        c = db["guilds"]
        data = c.find_one({"id": context.guild.id})

        newdata = {
                "$set": { "system_prompt": prompt }
        }

        c.update_one(
            { "id": context.guild.id }, newdata
        )

        await context.send("System prompt set to: " + prompt)

    @commands.hybrid_command(
        name="get_system_prompt",
        description="Get the system prompt for the AI",
        usage="get_system_prompt"
    )
    async def get_system_prompt(self, context: Context) -> None:
        c = db["guilds"]
        data = c.find_one({"id": context.guild.id})

        await context.send("System prompt is: " + data["system_prompt"])

    @commands.hybrid_command(
        name="reset_ai",
        description="Reset AI data",
        usage="reset_ai"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_messages=True)
    async def reset_ai(self, context: Context) -> None:
        c = db["ai_convos"]
        c.delete_one({"id": context.channel.id})
        await context.send("AI data reset for " + context.channel.mention)

    @commands.hybrid_command(
        name="toggle_ai",
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
