"""
Created on December 29, 2022

@author: arno

Controller part for searching crypto coins on website / exchanges

"""
import argparse
import re

import config
import DbHelper
from CoinData import CoinData, CoinSearchData
from CoinSearch import CoinSearch, SearchMethod
from CoinSearchAlcor import CoinSearchAlcor
from CoinSearchCoingecko import CoinSearchCoingecko
from CoinSearchCryptowatch import CoinSearchCryptowatch
from CoinSearchViewCli import CoinSearchViewCli
from CoinViewData import CoinInsertStatus
from Db import Db
from DbHelper import DbTableName, DbWebsiteName
from DbPostgresql import DbPostgresql
from DbSqlite3 import DbSqlite3


class CoinSearchController():
    """Controller for getting prices from crypto exchanges
    """

    def __init__(self, view: CoinSearchViewCli, search_prg: CoinSearch, db: Db) -> None:
        self.view = view
        self.search_prg = search_prg
        self.db = db

    def run(self):
        self.view.ui_root(self)

    def get_website(self) -> str:
        return self.search_prg.website

    def search_website(self, searchstr: str) -> list[CoinSearchData]:
        return self.search_prg.search(searchstr)

    def search_db(self, searchstr: str) -> list[CoinData]:
        return self.search_prg.search_id_db(self.db, searchstr)

    def insert_coin(self, coin: CoinSearchData) -> CoinInsertStatus:
        """Insert coin in database

        The coin is inserted into the table, if it doesn't already exists
        """
        # check if coin name, symbol is already in our database
        if not self.db.has_connection():
            return CoinInsertStatus.NO_DATABASE

        # if table doesn't exist, create table coins
        if not self.db.check_table(DbTableName.coin.name):
            DbHelper.create_coin_table(self.db)

        website_id = self.search_prg.get_website_id(self.db)

        db_result = DbHelper.get_coin(self.db, coin.coin.siteid, website_id)
        if len(db_result):
            return CoinInsertStatus.COIN_EXISTS

        # add new row to table coins
        result = DbHelper.insert_coin(self.db, coin.coin, website_id)
        if result <= 0:
            return CoinInsertStatus.INSERT_ERROR

        # safe coin images
        images_urls = {'thumb': coin.image_thumb,
                       'large': coin.image_large}
        self.search_prg.save_images(images_urls, coin.coin.name)
        return CoinInsertStatus.INSERT_OK


def __main__():
    """Search assets and store in database
    """
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-c', '--coin', type=str,
                           help='Coin name to search')
    argparser.add_argument('-w', '--website', type=str,
                           help='Website / exchange to search on')
    argparser.add_argument('-ch', '--chain', type=str,
                           help='Alcor: Chain name to search on Alcor')
    argparser.add_argument('-i', '--image', action='store_true',
                           help='Coingecko: Save image file for all coins from coingecko in database')
    argparser.add_argument('-s', '--searchweb', action='store_true',
                           help='Coingecko: Search directly from CoinGecko website instead or first retrieving list of all assets')
    args = argparser.parse_args()
    coin_search = args.coin
    download_all_images = args.image

    if args.searchweb:
        search_method = SearchMethod.WEB
    else:
        search_method = SearchMethod.ASSETS

    # Select chain from argument or take default all chains (only for Alcor)
    chain_str = args.chain
    if chain_str != None:
        chains = re.split('[;,]', chain_str)
    else:
        chains = config.ALCOR_CHAINS

    # init session
    if args.website == DbWebsiteName.alcor.name:
        cs = CoinSearchAlcor(chains=chains)
    elif args.website == DbWebsiteName.cryptowatch.name:
        cs = CoinSearchCryptowatch()
    else:
        cs = CoinSearchCoingecko(search_method=search_method)

    if config.DB_TYPE == 'sqlite':
        db = DbSqlite3(config.DB_CONFIG)
    elif config.DB_TYPE == 'postgresql':
        db = DbPostgresql(config.DB_CONFIG)
    else:
        raise RuntimeError('No database configuration')

    db.check_db()
    db_table_exist = db.check_table(DbTableName.coin.name)

    if download_all_images:
        if db_table_exist:
            cs = CoinSearchCoingecko()
            cs.download_images(db)
            print('Done downloading images')
        else:
            print('No database, exiting')
        exit()

    view = CoinSearchViewCli()
    app = CoinSearchController(view, cs, db)
    app.run()


if __name__ == '__main__':
    __main__()
