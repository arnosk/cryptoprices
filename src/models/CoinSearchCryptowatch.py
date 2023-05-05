"""
Created on Apr 23, 2022

@author: arno

Cryptowat.ch search

"""
import re

import config
import src.func.helperfunc as helperfunc
from src.data.CoinData import CoinData, CoinSearchData
from src.data.DbData import DbWebsiteName
from src.models.CoinSearch import CoinSearch


class CoinSearchCryptowatch(CoinSearch):
    """Class for searching a coin on the cryptowatch website
    """

    def __init__(self) -> None:
        self.website = DbWebsiteName.CRYPTOWATCH.name.lower()
        self.assets: list = []
        self.id_assets: int = 0
        super().__init__()

        # Update header of request session with user API key
        self.req.update_header({'X-CW-API-Key': config.CRYPTOWATCH_API})

    def search_id_assets(self, search_str: str) -> list[CoinSearchData]:
        """Search for coin in list of all assets
        """
        s = search_str.lower()
        resp_coins = [item for item in self.assets
                      if (re.match(s, item['sid'].lower()) or
                          re.match(s, item['name'].lower()) or
                          re.match(s, item['symbol'].lower()))]
        coinsearch = self.convert_assets_to_coinsearchdata(resp_coins)
        return coinsearch

    def convert_assets_to_coinsearchdata(self, resp: list) -> list[CoinSearchData]:
        """Convert result from site to list of CoinSearchData

        resp = list from the web
        example of resp['result']:
                [	{		
                    id:	182298
                    sid:	zer0zer0,
                    symbol:	0
                    name:	zer0zer0,
                    fiat:	false,
                    route:	https://api.cryptowat.ch/assets/00
                },		
        """
        coinsearch = []
        for r in resp:
            coindata = CoinData(siteid=r['sid'],
                                name=r['name'],
                                symbol=r['symbol'])
            coinsearch.append(CoinSearchData(coin=coindata,
                                             route=r['route']))
        return coinsearch

    def search(self, coin_search: str) -> list[CoinSearchData]:
        """Search coins from Cryptowatch assets
        """
        # check if assets are already loaded for today
        id_date = helperfunc.get_date_identifier()
        if self.id_assets != id_date:
            print('----------------loading all assets data--------------')
            self.assets = self.get_all_assets()
            self.id_assets = id_date

        # Do search on cryptowatch assets in memory
        cs_result = self.search_id_assets(coin_search)
        return cs_result

    def get_all_assets(self) -> list:
        '''Retrieve all assets from cryptowatch api
        '''
        url = f'{config.CRYPTOWATCH_URL}/assets'
        resp = self.req.get_request_response(url)
        coin_assets = resp['result']
        return coin_assets
