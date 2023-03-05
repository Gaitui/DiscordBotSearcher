import discord
from discord import app_commands
from discord.ext import commands, tasks
import logging
import asyncio
import json
from src.common import readJson
import threading
from src.autoShopeeSearch import autoShopeeSearch, autoSearchRun
import random
import time
import pandas as pd

class autoShopee(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.isRun = False
        self.modify = False
        self.check = None
        self.initPage = 3
        self.maxPage = 1
        self.minWait = 60
        self.maxWait = 90
        self.searchStatus = {}
        self.searchStatusLock = threading.Lock()
        self.searchData = {}

    @app_commands.command(name='shopeeadd', description='Add keyword into Shopee auto search.')
    async def shopeeadd(self, interaction, keyword: str):
        logging.info('Receive %(user)s(%(channel)s) shopeeadd command',
                     {'user': interaction.user, 'channel': interaction.channel.id})
        if len(keyword) == 0:
            await interaction.response.send_message('窩不知道你要搜尋什麼...')
            return
        initData = {"blacklist": [], "wait": 0}
        channelid = str(interaction.channel.id)
        status, searchData = readJson('autoShopeeData/searchData.json')
        if status:
            if searchData.__contains__(keyword):
                if searchData[keyword].__contains__(channelid):
                    await interaction.response.send_message('已有儲存此關鍵字...')
                    return
                else:
                    searchData[keyword][channelid] = initData
            else:
                searchData[keyword] = {channelid: initData}
        else:
            searchData = {keyword: {channelid: initData}}

        with open('autoShopeeData/searchData.json', 'w+', encoding='utf8') as file:
            file.write(json.dumps(searchData, indent=4))
            self.modify = True

        await interaction.response.send_message('儲存完成!')

    @app_commands.command(name='shopeedelete', description='Delete keyword from Shopee auto search.')
    async def shopeedelete(self, interaction, keyword: str):
        logging.info('Receive %(user)s(%(channel)s) shopeedelete command',
                     {'user': interaction.user, 'channel': interaction.channel.id})
        if len(keyword) == 0:
            await interaction.response.send_message('窩不知道你要刪什麼...')
            return
        channelid = str(interaction.channel.id)
        if self.searchStatus.__contains__(keyword) and channelid in self.searchStatus[keyword]['channel']:
            await interaction.response.send_message(f'看起來{keyword}正在執行，請先使用/shopeestop停止後再刪除')
            return
        status, searchData = readJson('autoShopeeData/searchData.json')
        if status and searchData.__contains__(keyword) and searchData[keyword].__contains__(channelid):
            searchData[keyword].pop(channelid)
            if len(searchData[keyword]) == 0:
                searchData.pop(keyword)
        else:
            await interaction.response.send_message('沒有儲存此關鍵字...')
            return

        with open('autoShopeeData/searchData.json', 'w+', encoding='utf8') as file:
            file.write(json.dumps(searchData, indent=4))
            self.modify = True

        await interaction.response.send_message('刪除完成，於下次循環開始生效~')


    @app_commands.command(name='shopeelist', description='Keywords in Shopee auto search.')
    async def shopeelist(self, interaction):
        logging.info('Receive %(user)s(%(channel)s) shopeelist command',
                     {'user': interaction.user, 'channel': interaction.channel.id})
        channelid = str(interaction.channel.id)
        status, searchData = readJson('autoShopeeData/searchData.json')
        if status:
            keys = []
            for keyword in searchData:
                if searchData[keyword].__contains__(channelid):
                    keys.append(keyword)
            if len(keys):
                key = '\n'.join(keys)
                await interaction.response.send_message(f"目前搜尋關鍵字:\n{key}")
            else:
                await interaction.response.send_message('目前沒有搜尋資料')
        else:
            await interaction.response.send_message('目前沒有搜尋資料')


    @app_commands.command(name='shopeeinfo', description='Return keyword info store in Shopee auto search.')
    async def shopeeinfo(self, interaction, keyword: str):
        logging.info('Receive %(user)s(%(channel)s) shopeeinfo command',
                     {'user': interaction.user, 'channel': interaction.channel.id})
        channelid = str(interaction.channel.id)
        status, searchData = readJson('autoShopeeData/searchData.json')
        if status and searchData.__contains__(keyword) and searchData[keyword].__contains__(channelid):
            embed = discord.Embed(title=keyword)
            embed.add_field(name="Ignore Words", value=','.join(searchData[keyword][channelid]["blacklist"]),
                            inline=False)
            embed.add_field(name="Wait Time", value=str(searchData[keyword][channelid]["wait"]), inline=False)
            if self.isRun and self.searchStatus.__contains__(keyword) and channelid in self.searchStatus[keyword]['channel']:
                embed.add_field(name="Status", value="Running", inline=False)
            else:
                embed.add_field(name="Status", value="Stop", inline=False)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f'目前沒有{keyword}的資料')


    @app_commands.command(name='shopeetimemodify', description='Modify wait time of keyword store in Shopee auto search.')
    async def shopeetimemodify(self, interaction, keyword: str, time: int):
        logging.info('Receive %(user)s(%(channel)s) shopeetimemodify command', {'user': interaction.user, 'channel': interaction.channel.id})
        if len(keyword) == 0:
            await interaction.response.send_message('窩不知道你要修改什麼...')
            return
        if time < 0:
            await interaction.response.send_message('時間必須大於等於0')
            return
        modify = False
        channelid = str(interaction.channel.id)
        status, searchData = readJson('autoShopeeData/searchData.json')
        if status and searchData.__contains__(keyword) and searchData[keyword].__contains__(channelid):
            if searchData[keyword][channelid]["wait"] != time:
                searchData[keyword][channelid]["wait"] = time
                modify = True
        else:
            await interaction.response.send_message('沒有儲存此關鍵字...')
            return
        if modify:
            with open('autoShopeeData/searchData.json', 'w+', encoding='utf8') as file:
                file.write(json.dumps(searchData, indent=4))
                self.modify = True
            await interaction.response.send_message('等待間隔修改完成，於下次循環開始生效~')
        else:
            await interaction.response.send_message('似乎沒有修改時間呢...')



    @app_commands.command(name='shopeeignoreadd',description='Add ignore words of keyword store in Shopee auto search.')
    async def shopeeignoreadd(self, interaction, keyword: str, ignore: str):
        logging.info('Receive %(user)s(%(channel)s) shopeeignoreadd command', {'user': interaction.user, 'channel': interaction.channel.id})
        if len(keyword) == 0:
            await interaction.response.send_message('窩不知道你的關鍵字...')
            return
        ignores = ignore.split()
        modify = False
        channelid = str(interaction.channel.id)
        status, searchData = readJson('autoShopeeData/searchData.json')
        if status and searchData.__contains__(keyword) and searchData[keyword].__contains__(channelid):
            for ig in ignores:
                if ig.lower() not in searchData[keyword][channelid]["blacklist"]:
                    searchData[keyword][channelid]["blacklist"].append(ig.lower())
                    modify = True
        else:
            await interaction.response.send_message('沒有儲存此關鍵字...')
            return
        if modify:
            with open('autoShopeeData/searchData.json', 'w+', encoding='utf8') as file:
                file.write(json.dumps(searchData, indent=4))
                self.modify = True
            await interaction.response.send_message('新增排除字眼完成，於下次循環開始生效~')
        else:
            await interaction.response.send_message('似乎沒有新增的排除字眼呢...')


    @app_commands.command(name='shopeeignoredelete', description='delete ignore words of keyword store in Shopee auto search.')
    async def shopeeignoredelete(self, interaction, keyword: str, ignore: str):
        logging.info('Receive %(user)s(%(channel)s) shopeeignoredelete command', {'user': interaction.user, 'channel': interaction.channel.id})
        if len(keyword) == 0:
            await interaction.response.send_message('窩不知道你的關鍵字...')
            return
        ignores = ignore.split()
        modify = False
        channelid = str(interaction.channel.id)
        status, searchData = readJson('autoShopeeData/searchData.json')
        if status and searchData.__contains__(keyword) and searchData[keyword].__contains__(channelid):
            for ig in ignores:
                if ig.lower() in searchData[keyword][channelid]["blacklist"]:
                    searchData[keyword][channelid]["blacklist"].remove(ig.lower())
                    modify = True
        else:
            await interaction.response.send_message('沒有儲存此關鍵字...')
            return
        if modify:
            with open('autoShopeeData/searchData.json', 'w+', encoding='utf8') as file:
                file.write(json.dumps(searchData, indent=4))
                self.modify = True
            await interaction.response.send_message('刪除排除字眼完成，於下次循環開始生效~')
        else:
            await interaction.response.send_message('似乎沒有需要刪除的排除字眼呢...')


    @app_commands.command(name='shopeerun', description='Add keyword into run list.')
    async def shopeerun(self, interaction, keyword: str):
        if not self.isRun:
            await interaction.response.send_message('請先執行/shopeeboot開始執行程序再加入')
            return
        channelid = str(interaction.channel.id)
        self.searchStatusLock.acquire()
        if self.searchStatus.__contains__(keyword):
            if channelid in self.searchStatus[keyword]['channel']:
                self.searchStatusLock.release()
                await interaction.response.send_message('關鍵字已在執行列...')
            else:
                self.searchStatus[keyword]['channel'].append(channelid)
                self.searchStatus[keyword]['time'] = int(time.time())
                self.searchStatusLock.release()
                await interaction.response.send_message('新增執行列完成，於下次循環開始生效~')
        else:
            status, searchData = readJson('autoShopeeData/searchData.json')
            if status and searchData.__contains__(keyword) and searchData[keyword].__contains__(channelid):
                self.searchStatus[keyword] = {'time': int(time.time()), 'channel': [channelid]}
                self.searchStatusLock.release()
                await interaction.response.send_message('新增執行列完成，於下次循環開始生效~')
            else:
                self.searchStatusLock.release()
                await interaction.response.send_message('沒有儲存此關鍵字...')


    @app_commands.command(name='shopeestop', description='Remove keyword from run list.')
    async def shopeestop(self, interaction, keyword: str):
        channelid = str(interaction.channel.id)
        self.searchStatusLock.acquire()
        if self.searchStatus.__contains__(keyword) and channelid in self.searchStatus[keyword]['channel']:
                self.searchStatus[keyword]['channel'].remove(channelid)
                if len(self.searchStatus[keyword]['channel'])== 0:
                    self.searchStatus.pop(keyword)
                self.searchStatusLock.release()
                await interaction.response.send_message('刪除執行列完成，於下次循環開始生效~')
        else:
            self.searchStatusLock.release()
            await interaction.response.send_message('似乎沒有在執行列呢..')

    @app_commands.command(name='shopeeboot', description='Start auto shopee.')
    async def shopeeboot(self, interaction):
        if self.isRun:
            await interaction.response.send_message('已經啟動了...')
            return
        self.isRun = True
        status, settings = readJson('Settings.json')
        if status:
            try:
                self.initPage = int(settings["INITPAGE"])
                self.maxPage = int(settings["MAXPAGE"])
                self.minWait = int(settings["AUTOWAITMIN"])
                self.maxWait = int(settings["AUTOWAITMAX"])
            except ValueError:
                await interaction.response.send_message('Settings.json設定錯誤，請檢查後再重新啟動')
                return
        else:
            await interaction.response.send_message('Settings.json開啟錯誤，請檢查後再重新啟動')
            return
        self.modify = True
        self.shopeerunning.start()
        await interaction.response.send_message('完成啟動Auto Shopee!')

    @app_commands.command(name='shopeeshutdown', description='Stop auto shopee.')
    async def shopeeshutdown(self, interaction):
        if self.isRun:
            self.isRun = False
            self.shopeerunning.stop()
            await interaction.response.send_message('已發出停止請求')
        else:
            await interaction.response.send_message('Auto Shopee並未執行或正在關閉')
        logging.info('isRun: %(isRun)s', {'isRun': self.isRun})

    @app_commands.command(name='shopeecheck', description='Check if auto shopee alive.')
    async def shopeecheck(self, interaction):
        if self.isRun:
            self.check = str(interaction.channel.id)
            await interaction.response.send_message('已發出檢查請求')
        else:
            await interaction.response.send_message('Auto Shopee並未執行或正在關閉')

    @tasks.loop(seconds=10)
    async def shopeerunning(self):
        if self.modify:
            status, self.searchData = readJson('autoShopeeData/searchData.json')
            self.modify = False
            if not status:
                await interaction.response.send_message('讀取searchData.json錯誤，請檢查後再重新啟動')
                return
        self.searchStatusLock.acquire()
        searchStatus = self.searchStatus
        self.searchStatusLock.release()
        for keyword in self.searchData:
            # logging.info('keyword: %(keyword)s', {'keyword': keyword})
            if self.check:
                channel = self.bot.get_channel(int(self.check))
                await channel.send('Auto Shopee正在執行!')
                self.check = None
            initSearch = False
            if searchStatus.__contains__(keyword) and searchStatus[keyword]['time'] < int(time.time()):
                logging.info('Start searching keyword: %(keyword)s', {'keyword': keyword})
                if searchStatus[keyword].__contains__('data'):
                    searchResult, addData = await autoShopeeSearch(keyword, searchStatus[keyword]['data'], self.maxPage)
                else:
                    readPath = 'autoShopeeData/' + keyword.replace(' ', '_') + '.csv'
                    try:
                        searchStatus[keyword]['data'] = pd.read_csv(readPath, index_col=0)
                        searchResult, addData = await autoShopeeSearch(keyword, searchStatus[keyword]['data'],self.maxPage)
                    except Exception as e:
                        logging.info('Cannot find %(keyword)s, start init search.', {'keyword': readPath})
                        logging.info('Exception: %(e)s', {'e': e})
                        searchResult, addData = await autoSearchRun(keyword, self.initPage)
                        logging.info('Init search finish.')
                        initSearch = True
                if searchResult:
                    logging.info('Keyword: %(keyword)s search success!', {'keyword': keyword})
                    if initSearch:
                        writePath = 'autoShopeeData/' + keyword.replace(' ', '_') + '.csv'
                        addData.to_csv(writePath)
                        self.searchStatusLock.acquire()
                        if self.searchStatus.__contains__(keyword):
                            self.searchStatus[keyword]['data'] = addData
                        self.searchStatusLock.release()
                    else:
                        if len(addData.index):
                            self.searchStatusLock.acquire()
                            self.searchStatus[keyword]['data'] = pd.concat(
                                [addData, self.searchStatus[keyword]['data']]).reset_index(drop=True)
                            self.searchStatusLock.release()
                            writePath = 'autoShopeeData/' + keyword.replace(' ', '_') + '.csv'
                            self.searchStatus[keyword]['data'].to_csv(writePath)
                            logging.info('Keyword: %(keyword)s has %(len)s new result!', {'keyword': keyword, 'len': len(addData.index)})
                            for channel in searchStatus[keyword]['channel']:
                                if self.searchData[keyword].__contains__(channel):
                                    if len(self.searchData[keyword][channel]['blacklist']):
                                        responsedf = addData[addData['Name'].str.lower().str.contains('|'.join(self.searchData[keyword][channel]['blacklist'])) == False].reset_index(drop=True)
                                    else:
                                        responsedf = addData
                                    logging.info('Keyword: %(keyword)s send %(len)s new result to %(channel)s!',
                                                 {'keyword': keyword, 'len': len(responsedf.index), 'channel': channel})
                                    if len(responsedf.index):
                                        channelid = self.bot.get_channel(int(channel))
                                        await channelid.send(f'關鍵字"{keyword}"搜尋到{len(responsedf.index)}個新結果')
                                        embeds = []
                                        embedsNow = -1
                                        for i in range(0, len(responsedf.index)):
                                            if i % 20 == 0:
                                                embeds.append(discord.Embed())
                                                embedsNow += 1
                                            embeds[embedsNow].add_field(
                                                name=f"商品名: {responsedf.loc[i]['Name']}\n價格: {responsedf.loc[i]['Price']}",
                                                value=f"https://shopee.tw/{responsedf.loc[i]['Name'].replace('#', '').replace(' ', '-')}-i.{responsedf.loc[i]['ShopId']}.{responsedf.loc[i]['Itemid']}",
                                                inline=False)
                                        for i in range(len(embeds)):
                                            await channelid.send(embed=embeds[i])
                    nextTime = 1e9
                    for channel in self.searchData[keyword]:
                        nextTime = min(nextTime, int(self.searchData[keyword][channel]['wait']))
                    logging.info('Keyword %(keyword)s next search start after %(nextTime)s s.', {'keyword': keyword, 'nextTime': nextTime})
                    self.searchStatusLock.acquire()
                    self.searchStatus[keyword]['time'] = int(time.time()) + nextTime
                    self.searchStatusLock.release()
                else:
                    logging.info('Keyword: %(keyword)s search Failed!', {'keyword': keyword})
                    await interaction.channel.send('搜尋發生錯誤')
                sleepTime = random.randint(self.minWait, self.maxWait)
                logging.info('Next Search start in %(sleepTime)s s.', {'sleepTime': sleepTime})
                await asyncio.sleep(sleepTime)
            if self.check:
                channel = self.bot.get_channel(int(self.check))
                await channel.send('Auto Shopee正在執行!')
                self.check = None



async def setup(bot: commands.Bot):
    await bot.add_cog(autoShopee(bot))
