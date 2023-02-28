import requests
import pandas as pd
from bs4 import BeautifulSoup
import json
import logging
import asyncio
import random
import re
import time

async def autoShopeeSearch(keyword, df1, pageNum):
    status, df = await autoSearchRun(keyword, pageNum)
    if status:
        keywordSplits = keyword.split(' ')
        for keywordSplit in keywordSplits:
            df = df[df['Name'].str.lower().str.contains(keywordSplit) == True]
        df2 = pd.merge(df.astype('str'), df1.astype('str'), on=['ShopId', 'Itemid'], how="left",
                       indicator=True) \
            .query('_merge=="left_only"') \
            .drop('_merge', axis=1) \
            .drop('Name_y', axis=1) \
            .drop('Price_y', axis=1) \
            .reset_index(drop=True)
        df2.rename(columns={'Name_x': 'Name', 'Price_x': 'Price'}, inplace=True)
        return True, df2
    else:
        return False, df


async def autoSearchRun(keyword, pageNum):
    df = pd.DataFrame(columns=['Name', 'Itemid', 'Price', 'ShopId'])
    try:
        res = requests.get('https://free-proxy-list.net/', timeout=12)
        ips = re.findall('\d+\.\d+\.\d+\.\d+:\d+', res.text)
        i = 0
        for ip in ips:
            try:
                url = 'https://shopee.tw/search?keyword=' + keyword + '&page=' + str(i) + '&sortBy=ctime'
                headers = {
                    'User-Agent': 'Googlebot',
                    'From': ''
                }
                r = requests.get(url, headers=headers, proxies={'https': f'http://{ip}/'}, allow_redirects=True, timeout=3)
                if r.status_code == requests.codes.ok:
                    logging.info('IP: %(ip)s Run success!', {'ip': ip})
                    soup = BeautifulSoup(r.text, 'html.parser')
                    articles = soup.select('[data-sqe="item"]')
                    articles_len = len(articles)
                    if articles_len == 0:
                        return True, df
                    for article in articles:
                        if not article.select('[data-sqe="ad"]'):
                            name = article.select('[data-sqe="name"] > div')[0].text
                            price = article.select('[data-sqe="name"]')[0].next_sibling.text
                            link = article.select('a')[0]['href']
                            iteminfo = link.split('-i.')[1].split('?sp_atk')[0]
                            shopid = iteminfo.split('.')[0]
                            itemid = iteminfo.split('.')[1]
                            df.loc[len(df.index)] = [name, itemid, price, shopid]
                    i += 1
                    if i >= pageNum:
                        return True, df
                else:
                    logging.info('Receive Status Code: %(code)s', {'code': r.status_code})
                await asyncio.sleep(random.randint(1, 5))
            except Exception as e:
                # logging.info('IP: %(ip)s Catch Exception! %(e)s', {'ip': ip, 'e': e})
                await asyncio.sleep(random.randint(1, 5))
        return True, df
    except Exception as e:
        logging.error(e)
        return False, df
