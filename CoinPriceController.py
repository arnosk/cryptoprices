"""
Created on December 29, 2022

@author: arno

Controller part for get prices of coins on website / exchanges

"""
import argparse
import re

import config
import src.db.DbHelper as DbHelper
from src.data.CoinData import CoinData, CoinPriceData
from src.db.Db import Db
from src.db.DbHelper import DbWebsiteName
from src.db.DbPostgresql import DbPostgresql
from src.db.DbSqlite3 import DbSqlite3
from src.models.CoinPrice import CoinPrice
from src.models.CoinPriceAlcor import CoinPriceAlcor
from src.models.CoinPriceCoingecko import CoinPriceCoingecko
from src.models.CoinPriceCryptowatch import CoinPriceCryptowatch
from src.views.CoinPriceViewCli import CoinPriceViewCli


class CoinPriceController():
    """Controller for getting prices from crypto exchanges
    """

    def __init__(self, view: CoinPriceViewCli, price_prg: CoinPrice, db: Db) -> None:
        self.view = view
        self.price_prg = price_prg
        self.db = db
        self.price_prg.attach_view_update_progress(self.view.update_progress)
        self.price_prg.attach_view_update_progress_text(
            self.view.update_progress_text)
        self.price_prg.attach_view_update_waiting_time(
            self.view.update_waiting_time)
        self.price_prg.website_id = DbHelper.get_website_id(
            self.db, self.price_prg.website)
        self.coin_data: list[CoinData] = []
        self.currency_data: list[str] = ['usd', 'eur', 'btc', 'eth']

    def get_website(self) -> str:
        return self.price_prg.website

    def get_price_current(self) -> list[CoinPriceData]:
        """Get current price
        """
        return self.price_prg.get_price_current(self.coin_data, self.currency_data)

    def get_price_hist(self, date: str) -> list[CoinPriceData]:
        """Get coingecko history price
        """
        return self.price_prg.get_price_hist(self.coin_data, self.currency_data, date)

    def get_price_hist_marketchart(self, date: str) -> list[CoinPriceData]:
        """Get history price of a coin or a token
        """
        return self.price_prg.get_price_hist_marketchart(self.coin_data, self.currency_data, date)

    def set_currency_data(self, currency_data: list[str]) -> None:
        """Set the currency data manual
        """
        self.currency_data = currency_data

    def set_coin_data(self, coin_data: list[CoinData]) -> None:
        """Set the coin data manual
        """
        self.coin_data = coin_data

    def load_coin_data_db(self) -> None:
        """Retrieve the coin data in database
        """
        if self.price_prg.website_id > 0:
            coins = DbHelper.get_coins(self.db, '', self.price_prg.website_id)
            self.coin_data = [CoinData(siteid=i[0], name=i[1], symbol=i[2], chain=i[3], base=i[4])
                              for i in coins]

    def run(self, coin_data: list[CoinData], date: str):
        """For now:

        1: Get current prices
        2: Get historical prices
        """
        self.coin_data = coin_data
        self.view.ui_root(self, date)


def __main__():
    """Search assets and store in database
    """
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-d', '--date', type=str,
                           help='Historical date to search, format: 2011-11-04T00:05:23+04:00',
                           default='2022-05-01T23:00')
    argparser.add_argument('-w', '--website', type=str,
                           help='Website / exchange to search on')
    argparser.add_argument('-c', '--coin', type=str,
                           help='List of coins to search', required=False)
    argparser.add_argument('-st', '--strictness', type=int,
                           help='Cryptowatch: Strictness type for filtering currency in base', default=1)
    argparser.add_argument('-mp', '--max_markets_per_pair', type=int,
                           help='Cryptowatch: Maximum markets per pair, 0 is no max', default=0)
    argparser.add_argument('-ch', '--chain', type=str,
                           help='Alcor: Chain to search on Alcor, only in combination with coin')

    args = argparser.parse_args()
    date = args.date
    coin_str = args.coin
    strictness = args.strictness
    max_markets_per_pair = args.max_markets_per_pair

    # init session
    search_website = str(args.website).lower()
    chain_str = ''
    if search_website == DbWebsiteName.ALCOR.name.lower():
        cp = CoinPriceAlcor()
        chain_str = args.chain if args.chain != None else 'proton'
    elif search_website == DbWebsiteName.CRYPTOWATCH.name.lower():
        cp = CoinPriceCryptowatch(
            strictness=strictness,
            max_markets_per_pair=max_markets_per_pair)
    else:
        cp = CoinPriceCoingecko()

    # init session
    if config.DB_TYPE == 'sqlite':
        db = DbSqlite3(config.DB_CONFIG)
    elif config.DB_TYPE == 'postgresql':
        db = DbPostgresql(config.DB_CONFIG)
    else:
        raise RuntimeError('No database configuration')

    # check if database and table coins exists and has values
    db.check_db()
    view = CoinPriceViewCli()
    app = CoinPriceController(view, cp, db)

    # Determine which coins to retrieve prices for
    # From arguments, from database, or take default
    if coin_str != None:
        coins = re.split('[;,]', coin_str)
        coin_data = [CoinData(siteid=i, chain=chain_str, symbol=i)
                     for i in coins]
    elif cp.website_id > 0:
        coins = DbHelper.get_coins(db, '', cp.website_id)
        coin_data = [CoinData(siteid=i[0], name=i[1], symbol=i[2], chain=i[3], base=i[4])
                     for i in coins]
    else:
        # providing default values for price retrieving
        if search_website == DbWebsiteName.ALCOR.name.lower():
            coins = [['proton', '157'], ['wax', '158'], ['proton', '13'], ['wax', '67'],
                     ['proton', '5'], ['eos', '2'], ['telos', '34'], ['proton', '96']]
            coin_data = [CoinData(siteid=i[1], chain=i[0]) for i in coins]
        elif search_website == DbWebsiteName.CRYPTOWATCH.name.lower():
            coins = ['btc', 'ltc', 'ada', 'sol', 'ardr', 'xpr']
            coin_data = [CoinData(siteid=i, symbol=i) for i in coins]
        else:
            coins = ['bitcoin', 'litecoin', 'cardano',
                     'solana', 'ardor', 'proton']
            coin_data = [CoinData(siteid=i) for i in coins]

    app.run(coin_data=coin_data, date=date)


if __name__ == '__main__':
    __main__()
