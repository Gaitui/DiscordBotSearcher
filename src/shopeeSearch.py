import requests
import pandas as pd
from bs4 import BeautifulSoup
import json
import logging


def shopeeSearch(keyword):
    with open('Settings.json', 'r', encoding='utf8') as file:
        settings = json.load(file)
        try:
            initPage = settings["INITPAGE"]
            initPage = int(initPage)
            maxPage = settings["MAXPAGE"]
            maxPage = int(maxPage)
        except ValueError:
            logging.error('MAXPAGE need to be an integer!')
            return False, False, None

    initSearch = False
    writePath = 'searchData/' + keyword.replace(' ', '_') + '.csv'
    try:
        df1 = pd.read_csv(writePath, index_col=0)
        pageNum = maxPage
    except:
        logging.info('Not find %(keyword)s.csv, set pageNum to initPage', {'keyword': keyword.replace(' ', '_')})
        pageNum = initPage
        initSearch = True

    status, df = searchRun(keyword, pageNum)
    if status:
        keywordSplits = keyword.split(' ')
        for keywordSplit in keywordSplits:
            df = df[df['Name'].str.lower().str.contains(keywordSplit) == True]
        if initSearch:
            df.to_csv(writePath)
            return True, False, df
        else:
            df2 = pd.merge(df.astype('str'), df1.astype('str'), on=['ShopId', 'Itemid'], how="left",
                           indicator=True) \
                .query('_merge=="left_only"') \
                .drop('_merge', axis=1) \
                .drop('Name_y', axis=1) \
                .drop('Price_y', axis=1) \
                .reset_index(drop=True)
            df2.rename(columns={'Name_x': 'Name', 'Price_x': 'Price'}, inplace=True)
            df = pd.concat([df2, df1]).reset_index(drop=True)
            df.to_csv(writePath)
            return True, True, df2
    else:
        return False, False, None


def searchRun(keyword, pageNum):
    df = pd.DataFrame(columns=['Name', 'Itemid', 'Price', 'ShopId'])
    try:
        for i in range(pageNum):
            url = 'https://shopee.tw/search?keyword=' + keyword + "&page=" + str(i) + "&sortBy=ctime"
            headers = {
                'User-Agent': 'Googlebot',
                'From': ''
            }
            r = requests.get(url, headers=headers, allow_redirects=True, stream=True)
            if r.status_code == requests.codes.ok:
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
            else:
                logging.error("Receive Status Code: %{code}s", {"code": r.status_code})
                return False, df
        return True, df
    except Exception as e:
        logging.error(e)
        return False, df
