import logging
import discord
from discord.ext import commands
import time
import json
from src.shopeeSearch import shopeeSearch
from discord import app_commands


class shopeeCmds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.time = time.time()
        self.load()

    def load(self):
        with open('Settings.json', 'r', encoding='utf8') as file:
            settings = json.load(file)
            waitTime = settings["WAITTIME"]
            try:
                self.waitTime = int(waitTime)
            except ValueError:
                logging.error('Wait Time need to be an integer!')
                exit(-1)

    @app_commands.command(name='shopee', description='Search new item at Shopee. (First Search will not return item)')
    async def shopee(self, interaction, keyword: str):
        logging.info('Receive %(author)s shopee search %(keyword)s command',
                     {'author': interaction.user, 'keyword': keyword})
        if len(keyword) == 0:
            await interaction.response.send_message('窩不知道你要搜尋什麼...')
            return
        if time.time() >= self.time:
            status, first, result = shopeeSearch(keyword)
            if status:
                if first:
                    await interaction.response.send_message(f'關鍵字"{keyword}"搜尋到{len(result.index)}個新結果')
                    embeds = []
                    embedsNow = -1
                    for i in range(0, len(result.index)):
                        if i % 20 == 0:
                            embeds.append(discord.Embed())
                            embedsNow += 1
                        embeds[embedsNow].add_field(
                            name=f"商品名: {result.loc[i]['Name']}\n價格: {result.loc[i]['Price']}",
                            value=f"https://shopee.tw/{result.loc[i]['Name'].replace(' ', '-')}-i.{result.loc[i]['ShopId']}.{result.loc[i]['Itemid']}",
                            inline=False)
                    for i in range(len(embeds)):
                        await interaction.channel.send(embed=embeds[i])
                else:
                    await interaction.response.send_message(f'關鍵字"{keyword}"初次搜尋完成，已記錄{len(result.index)}個結果')
            else:
                await interaction.response.send_message('搜尋時發生錯誤，請稍後再嘗試')
            self.time = int(time.time()) + self.waitTime
            del result
        else:
            await interaction.response.send_message(f'冷卻時間剩餘 {self.time - int(time.time())} 秒')


async def setup(bot):
    await bot.add_cog(shopeeCmds(bot))
