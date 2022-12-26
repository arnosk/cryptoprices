"""
Created on December 26, 2022

@author: arno

Command editor UI for get prices of coins on website / exchanges

"""
import argparse
import json
import re
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import pandas as pd

import config
import DbHelper
import helperfunc
from CoinData import CoinData, CoinPriceData
from CoinPriceAlcor import CoinPriceAlcor
from CoinPriceCoingecko import CoinPriceCoingecko
from CoinPriceCryptowatch import CoinPriceCryptowatch
from DbHelper import DbTableName, DbWebsiteName
from DbPostgresql import DbPostgresql
from DbSqlite3 import DbSqlite3


class AppCmdPrice:
    """UI class for getting prices in command editor
    """

    def show_progress(self, nr: int, total: int):
        """Show progress to standard output
        """
        print(f'\rRetrieving nr {nr:3d} of {total}', end='', flush=True)
        #sys.stdout.write(f'Retrieving nr {nr:3d} of {total}\r')
        # sys.stdout.flush()

    def write_to_file(self, pricedata: list[CoinPriceData], output_csv: str, output_xls: str, suffix: str):
        """Write a dataframe to a csv file and/or excel file

        pricedata = list of CoinPriceData
        output_csv = base filename for csv output file
        output_xls = base filename for xlsx output file
        suffix = last part of filename

        filename CSV file = config.OUTPUT_PATH+output_csv+suffix.csv
        filename XLS file = config.OUTPUT_PATH+output_xls+suffix.xlsx
        """
        if pricedata == []:
            print('Empty pricedata list, nothing to save')
            return

        df = self._convert_pricedata_to_df(pricedata)

        suffix = re.sub(r'[:;,!@#$%^&*()]', '', suffix)
        outputpath = config.OUTPUT_PATH
        if outputpath != '':
            outputpath = outputpath + '\\'

        if output_csv is not None:
            filepath = Path(f'{outputpath}{output_csv}{suffix}.csv')
            filepath.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(filepath)
            print(f'File written: {filepath}')

        if output_xls is not None:
            # remove timezone, because excel cannot handle this
            df['date'] = helperfunc.remove_tz(df['date'])
            filepath = Path(f'{outputpath}{output_xls}{suffix}.xlsx')
            filepath.parent.mkdir(parents=True, exist_ok=True)
            df.to_excel(filepath)
            print(f'File written: {filepath}')

    def print_coinpricedata(self, pricedata: list[CoinPriceData]) -> None:
        """Print price data to output

        pricedata = list of CoinPriceData
        """
        if pricedata == []:
            print('Empty pricedata list, nothing to print')
            return

        # init pandas displaying
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_colwidth', 25)
        pd.set_option('display.float_format', '{:.6e}'.format)

        df = self._convert_pricedata_to_df(pricedata)
        print(df)
        print()

    def _convert_pricedata_to_df(self, pricedata: list[CoinPriceData]) -> pd.DataFrame:
        """Converts list of objects to a pandas DataFrame

        json_normalize is used this way to flatten the coindata object inside the pricedata

        coindata = list of CoinPriceData

        returns pandas DataFrame
        """
        df = pd.json_normalize(data=[asdict(obj) for obj in pricedata])
        df.sort_values(by=['coin.name', 'curr'],
                       key=lambda col: col.str.lower(), inplace=True)
        return df

    def print_markets(self, markets) -> None:
        """Print cryptowatch markets
        """
        print()
        if len(markets) == 0:
            print('No market data loaded\n')
            return
        print('* Available markets of coins')
        resdf = pd.DataFrame(markets)
        resdf_print = resdf.drop('route', axis=1)
        print(resdf_print)
        print()

    def show_allowance(self, allowance):
        """Show allowance data to standard output on same row
        """
        allowance_str = json.dumps(allowance)[1:50]
        print('\r'+allowance_str.rjust(80), end='', flush=True)


def __main__():
    """Search assets and store in database
    """
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-d', '--date', type=str,
                           help=f'Historical date to search, format: 2011-11-04T00:05:23+04:00',
                           default='2022-05-01T23:00')
    argparser.add_argument('-w', '--website', type=str,
                           help='Website / exchange to search on')
    argparser.add_argument('-c', '--coin', type=str,
                           help=f'List of coins to search', required=False)
    argparser.add_argument('-oc', '--output_csv', type=str,
                           help='Filename and path to output CSV file', required=False)
    argparser.add_argument('-ox', '--output_xls', type=str,
                           help='Filename and path to the output Excel file', required=False)
    argparser.add_argument('-st', '--strictness', type=int,
                           help='Cryptowatch: Strictness type for filtering currency in base', default=1)
    argparser.add_argument('-mp', '--max_markets_per_pair', type=int,
                           help='Cryptowatch: Maximum markets per pair, 0 is no max', default=0)
    argparser.add_argument('-ch', '--chain', type=str,
                           help='Alcor: Chain to search on Alcor')

    args = argparser.parse_args()
    date = args.date
    coin_str = args.coin
    output_csv = args.output_csv
    output_xls = args.output_xls
    strictness = args.strictness
    max_markets_per_pair = args.max_markets_per_pair
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M')
    print('Current date:', current_date)

    # init session
    search_website = args.website
    chain_str = ''
    if search_website == DbWebsiteName.alcor.name:
        cp = CoinPriceAlcor()
        chain_str = args.chain if args.chain != None else 'proton'
    elif search_website == DbWebsiteName.cryptowatch.name:
        cp = CoinPriceCryptowatch(strictness=strictness)
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

    curr = ['usd', 'eur', 'btc', 'eth']

    # for coingecko, token prices
    chain = 'binance-smart-chain'
    contracts = ['0x62858686119135cc00C4A3102b436a0eB314D402',
                 '0xacfc95585d80ab62f67a14c566c1b7a49fe91167']

    app = AppCmdPrice()

    print('* Current price of coins')
    price = cp.get_price_current(coin_data, curr)
    app.print_coinpricedata(price)
    app.write_to_file(price, output_csv, output_xls,
                      f'_current_coins_{current_date}')
    print()

    if cp.website == DbWebsiteName.coingecko.name:
        print('* History price of coins')
        price = cp.get_price_hist(coin_data, curr, date)
        app.print_coinpricedata(price)
        app.write_to_file(price, output_csv, output_xls,
                          f'_hist_{date}')
        print()

    print('* History price of coins via market_chart')
    price = cp.get_price_hist_marketchart(coin_data, curr, date)
    app.print_coinpricedata(price)
    app.write_to_file(price, output_csv, output_xls,
                      f'_hist_marketchart_{date}')
    print()


if __name__ == '__main__':
    __main__()
