"""
Created on Mar 29, 2022

@author: arno

Coingecko search
Search id for coins to finally get price from coingecko
Search if coin already is in database
Put choosen coin in database and downloads coin image

Response is a dictionary with keys
coins, exchanges, icos, categories, nfts
the key coins has a list of the search result of coins
{
  'coins': [
    {
      'id': 'astroelon',
      'name': 'AstroElon',
      'symbol': 'ELONONE',
      'market_cap_rank': null,
      'thumb': 'https://assets.coingecko.com/coins/images/16082/thumb/AstroElon.png',
      'large': 'https://assets.coingecko.com/coins/images/16082/large/AstroElon.png'
    }
  ],
  'exchanges': [] ...
"""
import argparse
import re

import config
import DbHelper
import helperfunc
from CoinData import CoinData, CoinSearchData
from CoinSearch import CoinSearch
from Db import Db
from DbHelper import DbTableName, DbWebsiteName
from DbPostgresql import DbPostgresql
from DbSqlite3 import DbSqlite3


class CoinSearchCoingecko(CoinSearch):
    """Class for searching a coin on the coingecko website
    """

    def __init__(self) -> None:
        self.website = DbWebsiteName.coingecko.name
        super().__init__()

    def insert_coin(self, db: Db, coin: CoinSearchData) -> int:
        """Insert a new coin to the coins table

        And download the thumb and large picture of the coin

        db = instance of Db
        coin = search data with retrieved coin info from web
        return value = rowcount or total changes 
        """
        query = f'INSERT INTO {DbTableName.coin.name} (website_id, siteid, name, symbol) VALUES(?,?,?,?)'
        args = (self.website_id,
                coin.coin.siteid,
                coin.coin.name,
                coin.coin.symbol)
        res = db.execute(query, args)
        db.commit()
        return res

    def save_images(self, image_urls: dict, coin_name: str):
        """Save image files for one coin

        image_urls = dict if urls for images
        coin_name = string with name of coin
        """
        folder = config.IMAGE_PATH
        if 'thumb' in image_urls:
            helperfunc.save_file(
                image_urls['thumb'], folder, f'coingecko_{coin_name}_thumb')
        if 'small' in image_urls:
            helperfunc.save_file(
                image_urls['small'], folder, f'coingecko_{coin_name}_small')
        if 'large' in image_urls:
            helperfunc.save_file(
                image_urls['large'], folder, f'coingecko_{coin_name}_large')

    def download_images(self, db: Db):
        """Download image files for all coins in database from Coingecko

        db = instance of Db
        """
        # Get all coingeckoid's from database
        self.website_id = DbHelper.get_website_id(db, self.website)
        coins = db.query(
            f'SELECT siteid FROM {DbTableName.coin.name} WHERE website_id = ?',
            (self.website_id,))
        coins = [i[0] for i in coins]

        # Retrieve coin info from coingecko
        for coin in coins:
            url = f'''{config.COINGECKO_URL}/coins/{coin}?
                    localization=false&
                    tickers=false&
                    market_data=false&
                    community_data=false&
                    developer_data=false&
                    sparkline=false
                '''
            resp = self.req.get_request_response(url)
            params_image = resp['image']

            # Save image files
            self.save_images(params_image, coin)

    def search_id_assets(self, search_str: str, assets) -> list[CoinSearchData]:
        """Search for coin in list of all assets

        search_str: str = string to search in assets
        assets = list of assets from Alcor
        return value = list with search results
        """
        s = search_str.lower()
        resp_coins = [item for item in assets
                      if (re.match(s, item['id'].lower()) or
                          re.match(s, item['name'].lower()) or
                          re.match(s, item['symbol'].lower()))]
        coinsearch = self.convert_assets_to_coinsearchdata(resp_coins)
        return coinsearch

    def convert_assets_to_coinsearchdata(self, resp: list) -> list[CoinSearchData]:
        """Convert result from site to list of CoinSearchData

        resp = list from the web
        return value = list of CoinSearchData

        example of resp['result']:
        [   {				
                id:	0chain,		
                symbol:	zcn,		
                name:	0chain,		
                platforms:	{		
                        ethereum:	0xb9ef770b6a5e12e45983c5d80545258aa38f3b78,
                        polygon-pos:	0x8bb30e0e67b11b978a5040144c410e1ccddcba30
                }			
            },				
        """
        coinsearch = []
        for r in resp:
            coindata = CoinData(siteid=r['id'],
                                name=r['name'],
                                symbol=r['symbol'])
            coinsearch.append(CoinSearchData(coin=coindata))
        return coinsearch

    def search_id_web(self, search_str: str) -> list[CoinSearchData]:
        """Search request to Coingecko

        search_str = string to search in assets
        return value = list with search results
        """
        url = f'{config.COINGECKO_URL}/search?query={search_str}'
        resp = self.req.get_request_response(url)
        coinsearch = self.convert_websearch_to_coinsearchdata(resp['coins'])
        return coinsearch

    def convert_websearch_to_coinsearchdata(self, resp: list) -> list[CoinSearchData]:
        """Convert result from site to list of CoinSearchData

        resp = list from the web
        return value = list of CoinSearchData

        example of resp['coins']:
            [	{		
                    id:	bitcoin,
                    name:	Bitcoin,
                    api_symbol:	bitcoin,
                    symbol:	BTC,
                    market_cap_rank:	1
                    thumb:	https://assets.coingecko.com/coins/images/1/thumb/bitcoin.png,
                    large:	https://assets.coingecko.com/coins/images/1/large/bitcoin.png
                },		
        """
        coinsearch = []
        for r in resp:
            coindata = CoinData(siteid=r['id'],
                                name=r['name'],
                                symbol=r['symbol'])
            coinsearch.append(CoinSearchData(coin=coindata,
                                             market_cap_rank=r['market_cap_rank'],
                                             image_thumb=r['thumb'],
                                             image_large=r['large'], ))
        return coinsearch

    def get_search_id_db_query(self) -> str:
        """Query for searching coin in database

        return value = query for database search with 
                       ? is used for the search item
        """
        coin_search_query = f'''SELECT siteid, name, symbol FROM {DbTableName.coin.name} WHERE
                                website_id = {self.website_id} AND
                                (siteid like ? or
                                 name like ? or
                                 symbol like ?
                                )
                            '''
        return coin_search_query

    def search(self, db: Db, coin_search: str, assets: list = []):
        """Search coins in own database (if table exists)

        Show the results

        Search coins from internet (Coingecko)
        Show the results

        User can select a row number, from the table of search results
        To add that coin to the coins table, if it doesn't already exists

        db = instance of Db
        coin_search = string to search in assets
        """
        # Check if coin already in database
        db_result = self.search_id_db(db, coin_search)
        self.print_search_result(db_result, 'Database')

        if len(assets) > 0:
            # Search through assets
            cs_result = self.search_id_assets(coin_search, assets)
        else:
            # Do search on coingecko
            cs_result = self.search_id_web(coin_search)
        self.print_search_result(cs_result, 'CoinGecko')

        # ask user which row is the correct answer
        self.input_coin_row(db, cs_result)

    def get_all_assets(self) -> list:
        """Get all assets from Coingecko

        result = {
            {'id': 'astroelon',
            'symbol': 'elonone',
            'name': 'AstroElon',
            'platforms': {
                'ethereum': '0x...'
                }
            },...
        }
        """
        url_list = f'{config.COINGECKO_URL}/coins/list?include_platform=true'
        resp = self.req.get_request_response(url_list)
        assets = resp['result']
        return assets


def __main__():
    """Get Coingecko search assets and store in databse

    Arguments:
    - coin to search
    - image, save image file for all coins in database
    """
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-c', '--coin', type=str,
                           help='Coin name to search on Coingecko')
    argparser.add_argument('-i', '--image', action='store_true',
                           help='Save image file for all coins in database')
    argparser.add_argument('-w', '--searchweb', action='store_true',
                           help='Search directly from CoinGecko website instead of first retrieving list of all assets')
    args = argparser.parse_args()
    coin_search = args.coin
    download_all_images = args.image
    searchweb = args.searchweb

    # init session
    cs = CoinSearchCoingecko()
    if config.DB_TYPE == 'sqlite':
        db = DbSqlite3(config.DB_CONFIG)
    elif config.DB_TYPE == 'postgresql':
        db = DbPostgresql(config.DB_CONFIG)
    else:
        raise RuntimeError('No database configuration')

    db.check_db()
    db_table_exist = db.check_table(DbTableName.coin.name)

    if searchweb:
        # search directly from coingecko
        coin_assets = []
    else:
        # get all assets from coingecko
        coin_assets = cs.get_all_assets()

    if download_all_images:
        if db_table_exist:
            cs.download_images(db)
        else:
            print('No database, exiting')
    else:
        while True:
            if coin_search == None:
                coin_search = input('Search for coin: ')
            cs.search(db, coin_search, coin_assets)
            coin_search = None


if __name__ == '__main__':
    __main__()
