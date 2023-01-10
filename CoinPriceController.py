"""
Created on December 29, 2022

@author: arno

Controller part for get prices of coins on website / exchanges

"""
import argparse
import re
from datetime import datetime
from xmlrpc.client import DateTime

import config
import DbHelper
from CoinData import CoinData
from CoinPrice import CoinPrice
from CoinPriceAlcor import CoinPriceAlcor
from CoinPriceCoingecko import CoinPriceCoingecko
from CoinPriceCryptowatch import CoinPriceCryptowatch
from CoinPriceViewCmd import CoinPriceViewCmd
from DbHelper import DbTableName, DbWebsiteName
from DbPostgresql import DbPostgresql
from DbSqlite3 import DbSqlite3


class CoinPriceController():
    """Controller for getting prices from crypto exchanges
    """

    def __init__(self, view: CoinPriceViewCmd, model: CoinPrice) -> None:
        self.view = view
        self.model = model

    def run(self, coin_data: list[CoinData], currencies: list[str], date: str, output_csv: str, output_xls: str):
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M')
        price = self.model.get_price_current(
            coin_data, currencies, self.view.update_progress)
        self.view.print_coinpricedata(
            f'* Current price of coins, {current_date}', price)
        self.view.write_to_file(price, output_csv, output_xls,
                                f'_current_coins_{current_date}')

        if self.model.website == DbWebsiteName.coingecko.name:
            price = self.model.get_price_hist(
                coin_data, currencies, date, self.view.update_progress)
            self.view.print_coinpricedata('* History price of coins', price)
            self.view.write_to_file(price, output_csv, output_xls,
                                    f'_hist_{date}')

        price = self.model.get_price_hist_marketchart(
            coin_data, currencies, date, self.view.update_progress)
        self.view.print_coinpricedata(
            '* History price of coins via market_chart', price)
        self.view.write_to_file(price, output_csv, output_xls,
                                f'_hist_marketchart_{date}')


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
    argparser.add_argument('-cu', '--currency', type=str,
                           help='List of currencies', required=False)
    argparser.add_argument('-oc', '--output_csv', type=str,
                           help='Filename and path to output CSV file', required=False)
    argparser.add_argument('-ox', '--output_xls', type=str,
                           help='Filename and path to the output Excel file', required=False)
    argparser.add_argument('-st', '--strictness', type=int,
                           help='Cryptowatch: Strictness type for filtering currency in base', default=1)
    argparser.add_argument('-mp', '--max_markets_per_pair', type=int,
                           help='Cryptowatch: Maximum markets per pair, 0 is no max', default=0)
    argparser.add_argument('-ch', '--chain', type=str,
                           help='Alcor: Chain to search on Alcor, only in combination with coin')

    args = argparser.parse_args()
    date = args.date
    coin_str = args.coin
    currency_str = args.currency
    output_csv = args.output_csv
    output_xls = args.output_xls
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

    if currency_str != None:
        curr = re.split('[;,]', currency_str)
    else:
        curr = ['usd', 'eur', 'btc', 'eth']

    # for coingecko, token prices
    chain = 'binance-smart-chain'
    contracts = ['0x62858686119135cc00C4A3102b436a0eB314D402',
                 '0xacfc95585d80ab62f67a14c566c1b7a49fe91167']

    view = CoinPriceViewCmd()
    app = CoinPriceController(view, cp)
    app.run(coin_data=coin_data,
            currencies=curr,
            date=date,
            output_csv=output_csv,
            output_xls=output_xls)


if __name__ == '__main__':
    __main__()
