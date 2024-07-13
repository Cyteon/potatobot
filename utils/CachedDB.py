# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon

import pymongo
import redis
import json
import logging
import time
import os
from bson import ObjectId

logger = logging.getLogger("discord_bot")

mongo_client_pool = pymongo.MongoClient(os.getenv("MONGODB_URL"), maxPoolSize=50)
mongo_db = mongo_client_pool.potatobot

redis_pool = redis.ConnectionPool.from_url(os.getenv("REDIS_URL"), max_connections=100)
redis_client = redis.Redis(connection_pool=redis_pool)

print("Connected to MongoDB at: ", mongo_client_pool.host)
print("Connected to Redis at: ", redis_client.connection_pool.connection_kwargs["host"])

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, bytes):
            return None  # Skip binary data
        return json.JSONEncoder.default(self, obj)

async def find_one(collection, query, ex=30):
    start_time = time.time() * 1000

    cache_key = f"{collection.name}:{json.dumps(query, cls=JSONEncoder)}"
    cached_result = redis_client.get(cache_key)

    if cached_result:
        logger.info(f"Cache hit for query {cache_key} - took {time.time() * 1000 - start_time:.2f}ms")
        return json.loads(cached_result)
    else:
        result = collection.find_one(query)

        if result:
            result = json.loads(JSONEncoder().encode(result))
            redis_client.set(cache_key, json.dumps(result), ex=ex)

        logger.info(f"Cache miss for query {cache_key} - took {time.time() * 1000 - start_time:.2f}ms")
        return result

async def update_one(collection, filter, update, upsert=False):
    result = collection.update_one(filter, update, upsert=upsert)

    cache_key = f"{collection.name}:{json.dumps(filter, cls=JSONEncoder)}"
    redis_client.delete(cache_key)

    return result

def sync_find_one(collection, query, ex=30):
    start_time = time.time() * 1000

    cache_key = f"{collection.name}:{json.dumps(query, cls=JSONEncoder)}"
    cached_result = redis_client.get(cache_key)

    if cached_result:
        logger.info(f"Cache hit for query {cache_key} - took {time.time() * 1000 - start_time:.2f}ms")
        return json.loads(cached_result)
    else:
        result = collection.find_one(query)

        if result:
            result = json.loads(JSONEncoder().encode(result))
            redis_client.set(cache_key, json.dumps(result), ex=ex)

        logger.info(f"Cache miss for query {cache_key} - took {time.time() * 1000 - start_time:.2f}ms")
        return result

def sync_update_one(collection, filter, update, upsert=False):
    result = collection.update_one(filter, update, upsert=upsert)

    cache_key = f"{collection.name}:{json.dumps(filter, cls=JSONEncoder)}"
    redis_client.delete(cache_key)

    return result
