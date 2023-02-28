import discord
from discord.ext import commands
import logging
from discord import app_commands


class events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            self.bot.tree.copy_global_to(guild=discord.Object(id=guild.id))
            await self.bot.tree.sync(guild=discord.Object(id=guild.id))
            logging.info('guild ID： %(guild)s', {'guild': guild.id})
        logging.info('Bot： %(user)s is Ready', {'user': self.bot.user})

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if message.content == 'ping':
            logging.info('Receive Ping Msg: %(ctx)s', {'ctx': message.author})
            await message.channel.send(self.bot.latency)


async def setup(bot):
    await bot.add_cog(events(bot))
