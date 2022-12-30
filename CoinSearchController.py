"""
Created on December 29, 2022

@author: arno

Controller part for searching crypto coins on website / exchanges

"""
import argparse
import re
import sys

import config
from CoinSearch import CoinSearch, SearchMethod
from CoinSearchAlcor import CoinSearchAlcor
from CoinSearchCoingecko import CoinSearchCoingecko
from CoinSearchCryptowatch import CoinSearchCryptowatch
from CoinSearchViewCmd import CoinSearchViewCmd, Command
from Db import Db
from DbHelper import DbTableName, DbWebsiteName
from DbPostgresql import DbPostgresql
from DbSqlite3 import DbSqlite3


class CoinPriceController():
    """Controller for getting prices from crypto exchanges
    """

    def __init__(self, view: CoinSearchViewCmd, model: CoinSearch, db: Db) -> None:
        self.view = view
        self.model = model
        self.db = db

    def run(self):
        self.view.ui_root(self.db, self.model)


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
        search_method = SearchMethod.web
    else:
        search_method = SearchMethod.assets

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
    app = CoinPriceController(view, cs, db)
    app.run()


if __name__ == '__main__':
    __main__()
