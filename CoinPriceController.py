"""
Created on December 29, 2022

@author: arno

Controller part for get prices of coins on website / exchanges

"""
import argparse
import re

import config
import DbHelper
from CoinData import CoinData, CoinPriceData
from CoinPrice import CoinPrice
from CoinPriceAlcor import CoinPriceAlcor
from CoinPriceCoingecko import CoinPriceCoingecko
from CoinPriceCryptowatch import CoinPriceCryptowatch
from CoinPriceViewCli import CoinPriceViewCli
from Db import Db
from DbHelper import DbTableName, DbWebsiteName
from DbPostgresql import DbPostgresql
from DbSqlite3 import DbSqlite3


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
            query = f'''SELECT chain, siteid, {DbTableName.coin.name}.name, symbol, base FROM {DbTableName.coin.name} 
                        LEFT JOIN {DbTableName.website.name} ON 
                        {DbTableName.coin.name}.website_id = {DbTableName.website.name}.id
                        WHERE {DbTableName.website.name}.name = "{self.get_website()}"
                    '''
            coins = self.db.query(query)
            self.coin_data = [CoinData(chain=i[0], siteid=i[1], name=i[2], symbol=i[3], base=i[4])
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
    search_website = args.website
    chain_str = ''
    if search_website == DbWebsiteName.alcor.name:
        cp = CoinPriceAlcor()
        chain_str = args.chain if args.chain != None else 'proton'
    elif search_website == DbWebsiteName.cryptowatch.name:
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
    db_table_exist = db.check_table(DbTableName.coin.name)
    if db_table_exist:
        cp.website_id = DbHelper.get_website_id(db, cp.website)

    # Determine which coins to retrieve prices for
    # From arguments, from database, or take default
    if coin_str != None:
        coins = re.split('[;,]', coin_str)
        coin_data = [CoinData(siteid=i, chain=chain_str, symbol=i)
                     for i in coins]
    elif cp.website_id > 0:
        query = f'''SELECT chain, siteid, {DbTableName.coin.name}.name, symbol, base FROM {DbTableName.coin.name} 
                    LEFT JOIN {DbTableName.website.name} ON 
                    {DbTableName.coin.name}.website_id = {DbTableName.website.name}.id
                    WHERE {DbTableName.website.name}.name = "{cp.website}"
                '''
        coins = db.query(query)
        coin_data = [CoinData(chain=i[0], siteid=i[1], name=i[2], symbol=i[3], base=i[4])
                     for i in coins]
    else:
        # providing default values for price retrieving
        if search_website == DbWebsiteName.alcor.name:
            coins = [['proton', '157'], ['wax', '158'], ['proton', '13'], ['wax', '67'],
                     ['proton', '5'], ['eos', '2'], ['telos', '34'], ['proton', '96']]
            coin_data = [CoinData(siteid=i[1], chain=i[0]) for i in coins]
        elif search_website == DbWebsiteName.cryptowatch.name:
            coins = ['btc', 'ltc', 'ada', 'sol', 'ardr', 'xpr']
            coin_data = [CoinData(siteid=i, symbol=i) for i in coins]
        else:
            coins = ['bitcoin', 'litecoin', 'cardano',
                     'solana', 'ardor', 'proton']
            coin_data = [CoinData(siteid=i) for i in coins]

    # for coingecko, token prices
    chain = 'binance-smart-chain'
    contracts = ['0x62858686119135cc00C4A3102b436a0eB314D402',
                 '0xacfc95585d80ab62f67a14c566c1b7a49fe91167']

    view = CoinPriceViewCli()
    app = CoinPriceController(view, cp, db)
    app.run(coin_data=coin_data, date=date)


if __name__ == '__main__':
    __main__()
