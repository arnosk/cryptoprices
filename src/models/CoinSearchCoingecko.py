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
import re

import config
import src.db.DbHelper as DbHelper
import src.func.helperfunc as helperfunc
from src.data.CoinData import CoinData, CoinSearchData
from src.db.Db import Db
from src.db.DbHelper import DbWebsiteName
from src.models.CoinSearch import CoinSearch, SearchMethod


class CoinSearchCoingecko(CoinSearch):
    """Class for searching a coin on the coingecko website
    """

    def __init__(self, search_method: SearchMethod = SearchMethod.WEB) -> None:
        super().__init__()
        self.website = DbWebsiteName.COINGECKO.name.lower()
        self.assets: list = []
        self.id_assets: int = 0
        self.search_method: SearchMethod = search_method

    def set_search_method(self, search_method: SearchMethod) -> None:
        self.search_method = search_method

    def save_images(self, image_urls: dict, coin_name: str):
        """Save image files for one coin
        """
        folder = config.IMAGE_PATH
        if 'thumb' in image_urls:
            helperfunc.save_file(
                image_urls['thumb'], folder, f'{self.website}_{coin_name}_thumb')
        if 'small' in image_urls:
            helperfunc.save_file(
                image_urls['small'], folder, f'{self.website}_{coin_name}_small')
        if 'large' in image_urls:
            helperfunc.save_file(
                image_urls['large'], folder, f'{self.website}_{coin_name}_large')

    def download_images(self, db: Db):
        """Download image files for all coins in database from Coingecko
        """
        # Get all coingeckoid's from database
        self.website_id = DbHelper.get_website_id(db, self.website)
        coins = DbHelper.get_coins(db, '', self.website_id)
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

    def search_id_assets(self, search_str: str) -> list[CoinSearchData]:
        """Search for coin in list of all assets
        """
        s = search_str.lower()
        resp_coins = [item for item in self.assets
                      if (re.match(s, item['id'].lower()) or
                          re.match(s, item['name'].lower()) or
                          re.match(s, item['symbol'].lower()))]
        coinsearch = self.convert_assets_to_coinsearchdata(resp_coins)
        return coinsearch

    def convert_assets_to_coinsearchdata(self, resp: list) -> list[CoinSearchData]:
        """Convert result from site to list of CoinSearchData

        resp = list from the web
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
        """
        url = f'{config.COINGECKO_URL}/search?query={search_str}'
        resp = self.req.get_request_response(url)
        coinsearch = self.convert_websearch_to_coinsearchdata(resp['coins'])
        return coinsearch

    def convert_websearch_to_coinsearchdata(self, resp: list) -> list[CoinSearchData]:
        """Convert result from site to list of CoinSearchData

        resp = list from the web
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

    def search(self, coin_search: str) -> list[CoinSearchData]:
        """Search from exchange (Coingecko)
        """
        if self.search_method == SearchMethod.ASSETS:
            # check if assets are already loaded for today
            id_date = helperfunc.get_date_identifier()
            if self.id_assets != id_date:
                print('----------------loading all assets data--------------')
                self.assets = self.get_all_assets()
                self.id_assets = id_date

            # Search through assets
            cs_result = self.search_id_assets(coin_search)
        else:
            # Do search on coingecko
            cs_result = self.search_id_web(coin_search)
        return cs_result

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
        url = f'{config.COINGECKO_URL}/coins/list?include_platform=true'
        resp = self.req.get_request_response(url)
        assets = resp['result']
        return assets
