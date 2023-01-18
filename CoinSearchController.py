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
from CoinSearchViewCmd import CoinSearchViewCmd
from Db import Db
from DbHelper import DbTableName, DbWebsiteName
from DbPostgresql import DbPostgresql
from DbSqlite3 import DbSqlite3


class CoinSearchController():
    """Controller for getting prices from crypto exchanges
    """

    def __init__(self, view: CoinSearchViewCmd, search_prg: CoinSearch, db: Db) -> None:
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

    def insert_coin_check(self, coin: CoinSearchData):
        """Check for existence of selected coin before inserting coin in database

        The selected coin is inserted into the table, if it doesn't already exists
        """
        coin_id = coin.coin.siteid
        coin_name = coin.coin.name

        # check if coin name, symbol is already in our database
        if self.db.has_connection():
            # if table doesn't exist, create table coins
            if not self.db.check_table(DbTableName.coin.name):
                DbHelper.create_coin_table(self.db)

            website_id = self.search_prg.handle_website_id(self.db)

            db_result = DbHelper.get_coin(self.db, coin_id, website_id)
            if len(db_result):
                self.view.show_insert_coin_result(
                    f'Database already has a row with the coin {coin_name}')
            else:
                # add new row to table coins
                insert_result = DbHelper.insert_coin(
                    self.db, coin.coin, website_id)
                if insert_result > 0:
                    self.view.show_insert_coin_result(
                        f'{coin_name} added to the database')

                    # safe coin images
                    images_urls = {'thumb': coin.image_thumb,
                                   'large': coin.image_large}
                    self.search_prg.save_images(images_urls, coin_name)
                else:
                    self.view.show_insert_coin_result(
                        f'Error adding {coin_name} to database')
        else:
            self.view.show_insert_coin_result('No database connection')


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

    view = CoinSearchViewCmd()
    app = CoinSearchController(view, cs, db)
    app.run()


if __name__ == '__main__':
    __main__()
