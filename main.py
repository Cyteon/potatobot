# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon

import os
import threading
import uvicorn
import json
import sys
from bson import ObjectId
from dotenv import load_dotenv
from typing import Optional

import ssl

from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware

from bot import DiscordBot

from utils import DBClient, CONSTANTS, CachedDB

db = DBClient.db

# Load environment variables
load_dotenv()

# Instantiate the bot and FastAPI app
bot = DiscordBot()
app = FastAPI()

if not os.path.isfile(f"{os.path.realpath(os.path.dirname(__file__))}/config.json"):
    sys.exit("'config.json' not found! Please add it and try again.")
else:
    with open(f"{os.path.realpath(os.path.dirname(__file__))}/config.json") as file:
        config = json.load(file)

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain("./ssl/potato-api.cyteon.tech.pem", keyfile="./ssl/potato-api.cyteon.tech.key")

origins = config["origins"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, bytes):
            return None  # Skip binary data
        return json.JSONEncoder.default(self, obj)

# Define a simple FastAPI route
@app.get("/")
async def read_root():
    return {"message": "User: " + bot.user.name + " is online! "}

@app.get("/api")
async def read_api_root():
    return {"message": "OK"}

@app.get("/api/commands/{cog}")
async def get_commands(cog: Optional[str] = "all"):
    if cog == "all":
        # Get all commands
        all_commands = [
            {
                "name": (cmd.parent.name + " " if cmd.parent else "") + cmd.name,
                "description": cmd.description,
                "cog": cmd.cog_name,
                "usage": cmd.usage, "aliases": cmd.aliases,
                "subcommand": cmd.parent != None
            } for cmd in bot.walk_commands() if not "owner" in cmd.cog_name.lower()
        ]
        return all_commands
    else:
        if cog not in bot.cogs:
            return {"message": "Cog not found.", "status": 404}

        if "owner" in cog:
            return {"message": "Cog not found.", "status": 404}

        commands = [
            {
                "name": (cmd.parent.name + " " if cmd.parent else "") + cmd.name,
                "description": cmd.description,
                "usage": cmd.usage, "aliases": cmd.aliases,
                "subcommand": cmd.parent != None
            } for cmd in bot.get_cog(cog).walk_commands()
        ]

        return commands

@app.get("/api/cogs")
async def get_cogs():
    cogs = list(bot.cogs.keys())
    if 'owner' in cogs:
        cogs.remove('owner')
    return cogs

@app.get("/api/guild/{id}")
async def get_guild(id: int):
    guild = bot.get_guild(id)

    if guild is None:
        return {"message": "Guild not found.", "status": 404}

    guilds = db["guilds"]
    guild_data = guilds.find_one({"id": guild.id})

    if guild_data is None:
        guild_data = CONSTANTS.guild_data_template(id)
        guilds.insert_one(guild_data)

    guild = {
        "name": guild.name,
        "id": guild.id,
        "dbdata": str(JSONEncoder().encode(guild_data)),
        "members": len(guild.members),
        "channels": len(guild.channels),
        "roles": len(guild.roles),
    }

    return guild

class UpdateModel(BaseModel):
    author: int
    newdata: str

@app.put("/api/guild/{id}/update", response_model=UpdateModel)
async def update_guild(id: int, data: UpdateModel):
    return {"message": "This endpoint is disabled for security", "status": 501}

    data = jsonable_encoder(data)

    guild = bot.get_guild(id)

    if guild.get_member(data["author"]).guild_permissions.administrator:
        guilds = db["guilds"]
        guild_data = guilds.find_one({"id": guild.id})

        if guild_data is None:
            guild_data = CONSTANTS.guild_data_template(id)
            guilds.insert_one(guild_data)

        guilds.update_one({"id": guild.id}, {"$set": json.loads(data["newdata"])})

        return data
    else:
        return {"message": "You do not have the required permissions.", "status": 403}


@app.get("/api/user/{id}")
async def get_user(id: int):
    user = bot.get_user(id)

    if user is None:
        return {"message": "User not found.", "status": 404}

    users = db["global_users"]
    user_data = await CachedDB.find_one(users, {"id": user.id})

    if user_data is None:
        user_data = CONSTANTS.user_global_data_template(id)
        users.insert_one(user_data)

    if user_data["blacklisted"]:
        return {"message": "User is blacklisted.", "status": 403, "reason": user_data["blacklist_reason"]}

    mutals = user.mutual_guilds

    guilds = []

    for guild in mutals:
        if guild.get_member(user.id).guild_permissions.administrator:
            guilds.append({
                "name": guild.name,
                "id": str(guild.id),
                "members": len(guild.members),
            })

    return {
        "name": user.name,
        "id": user.id,
        "guilds": guilds
    }

@app.get("/api/stats")
async def get_stats():
    return {
        "commands_ran": bot.statsDB.get("commands_ran"),
        "users": len(set(bot.get_all_members())),
        "ai_requests": bot.statsDB.get("ai_requests"),
    }
# Function to run FastAPI
def run_fastapi():
    uvicorn.run(
        app, host="0.0.0.0",
        port=443,
        ssl_keyfile=config["ssl_keyfile"],
        ssl_certfile=config["ssl_certfile"],
        ssl_version=ssl.PROTOCOL_TLS
    )

# Run FastAPI in a separate thread
thread = threading.Thread(target=run_fastapi)
thread.start()

# Run the Discord bot
TOKEN = os.getenv("TOKEN")
bot.run(TOKEN)
