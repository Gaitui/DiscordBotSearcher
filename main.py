import json
import logging
from time import gmtime, strftime
from discord.ext import commands
import discord
import os
import asyncio

LOGGING_FORMAT = '%(asctime)s [%(levelname)-8s] %(message)s'
logging.basicConfig(level=logging.INFO, filename='log/bot_out.log', filemode='a+', format=LOGGING_FORMAT)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)

async def main():
    async with bot:
        await load_extensions()
        await bot.start(token)


async def load_extensions():
    for file in os.listdir('./cogs'):
        if file.endswith('.py'):
            await bot.load_extension(f'cogs.{file[:-3]}')


with open('Settings.json', 'r', encoding='utf8') as file:
    settings = json.load(file)
    token = settings["TOKEN"]
    logging.info('Token: %(token)s', {'token': token})

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.error(e)
        logging.info('Process Shutdown!')
    except:
        logging.info('Process Shutdown!')
