import asyncio
from time import sleep
from datetime import datetime
from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings 
import pymongo

client = AsyncIOMotorClient(settings.db_uri)
db = client.wudn

async def seed(db):
    await db["Properties"].create_index([('address',pymongo.TEXT),('type',pymongo.TEXT),('title',pymongo.TEXT)])
    await db["Users"].insert_one({
        "email":"wudn-temp@instaddr.ch",
        "password": CryptContext(schemes=["bcrypt"], deprecated="auto").hash("Password123!"),
        "name":"admin",
        "role":"admin",
        "state":"created",
        "createdAt":datetime.now(),
        "family_name":"admin",
        "favourite":[],
        "gender":"Male",
        "given_name":"admin",
        "history":[],
        "modifiedAt":datetime.now(),
    })

async def drop(db):
    await client.drop_database('wudn')

if __name__=="__main__":
    loop=asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    client = AsyncIOMotorClient(settings.db_uri, io_loop=loop)
    db = client.wudn
    loop.run_until_complete(seed(db))