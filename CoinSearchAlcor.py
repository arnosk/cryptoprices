"""
Created on October 15, 2022

@author: arno

Class CoinSearchAlcor

"""
import argparse
import re

import config
import helperfunc
from CoinData import CoinData, CoinSearchData
from CoinSearch import CoinSearch
from Db import Db
from DbHelper import DbTableName, DbWebsiteName
from DbPostgresql import DbPostgresql
from DbSqlite3 import DbSqlite3


class CoinSearchAlcor(CoinSearch):
    """Class for searching a coin on the alcor exchange
    """

    def __init__(self) -> None:
        self.website = DbWebsiteName.alcor.name
        self.assets: dict = {}
        self.id_assets: int = 0
        super().__init__()

    def search_id_assets(self, search_str: str) -> list[CoinSearchData]:
        """Search for coin in list of all assets

        search_str: str = string to search in assets
        assets = list of assets from Alcor
        return value = list with search results
        """
        s = search_str.lower()
        resp_coins = []
        for asset in self.assets.values():
            resp_coin = [item for item in asset
                         if (re.match(s, item['base_token']['symbol']['name'].lower()) or
                             re.search(s, item['base_token']['str'].lower()) or
                             re.match(s, item['quote_token']['symbol']['name'].lower()) or
                             re.search(s, item['quote_token']['str'].lower()))]
            resp_coins.extend(resp_coin)
        coinsearch = self.convert_assets_to_coinsearchdata(resp_coins)
        return coinsearch

    def convert_assets_to_coinsearchdata(self, resp: list) -> list[CoinSearchData]:
        """Convert result from site to list of CoinSearchData

        resp = list from the web
        return value = list of CoinSearchData

        {'id': 157,
        'base_token': {"symbol":{"name":"XUSDC","precision":6},"contract":"xtokens","str":"XUSDC@xtokens"},
        'quote_token': {"symbol":{"name":"FREEOS","precision":4},"contract":"freeostokens","str":"FREEOS@freeostokens"},
        'chain': 'proton',
        'ticker_id': 'FREEOS-freeostokens_XUSDC-xtokens',
        'volume24': 0, 'volumeWeek': 0, 'volumeMonth': 0,
        'change24': 0, 'changeWeek': 0,
        'frozen': false
        }
        """
        coinsearch = []
        for r in resp:
            coindata = CoinData(siteid=r['id'],
                                name=r['quote_token']['str'],
                                symbol=r['quote_token']['symbol']['name'],
                                chain=r['chain'],
                                base=r['base_token']['str'])
            coinsearch.append(CoinSearchData(coin=coindata,
                                             base=r['base_token']['symbol']['name'],
                                             volume=r['volumeWeek'],
                                             change=r['changeWeek']))
        return coinsearch

    def search(self, db: Db, coin_search: str, chains: list) -> list[CoinSearchData]:
        """Search coins in own database (if table exists)

        Search coins from Alcor assets (already in assets)
        Show the results

        db = instance of Db
        coin_search = string to search in assets
        chains = list of the alcor chains to search on
        self.assets = dictionary where each key is a chain with a list of string with assets from Alcor
        """
        # check if assets are already loaded for all chains and today
        id_date = helperfunc.get_date_identifier()
        if self.id_assets != id(chains) + id_date:
            print('----------------loading all assets data--------------')
            self.assets = self.get_all_assets(chains)
            self.id_assets = id(chains) + id_date

        # Do search on Alcor assets in memory
        cs_result = self.search_id_assets(coin_search)
        return cs_result

    def get_all_assets(self, chains: list) -> dict:
        '''Retrieve all assets from alcor api

        chains = list of chains in alcor ecosystem

        returns = dictionary where each key is a chain with a list of string with assets from Alcor
        '''
        coin_assets = {}
        for chain in chains:
            url = f'{config.ALCOR_URL.replace("?", chain)}/markets'
            resp = self.req.get_request_response(url)
            coin_assets[chain] = resp['result']
        return coin_assets
