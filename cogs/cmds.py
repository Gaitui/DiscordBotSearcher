import logging
import discord
from discord.ext import commands
from discord import app_commands

class cmds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='ping', description='Return server ping')
    async def ping(self, interaction: discord.Interaction):
        logging.info('Receive %(author)s ping command', {'author': interaction.channel.id})
        await interaction.response.send_message(self.bot.latency)


async def setup(bot):
    await bot.add_cog(cmds(bot))
