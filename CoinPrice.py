"""
Created on October 15, 2022

@author: arno

Base Class CoinPrice

"""
import json
import re
from abc import ABC, abstractmethod
from argparse import ArgumentParser
from dataclasses import asdict
from pathlib import Path

import pandas as pd

import config
import helperfunc
from CoinData import CoinData, CoinPriceData
from RequestHelper import RequestHelper


class CoinPrice(ABC):
    """Base class for looking up the price of a coin on an exchange or provider
    """
    website: str

    def __init__(self) -> None:
        self.website_id: int = 0
        self.req = RequestHelper()
        self.nr_try_max: int = 10

    @abstractmethod
    def get_price_current(self, coindata: list[CoinData], currencies: list[str]) -> list[CoinPriceData]:
        """Get current price

        coindata = list of CoinData for market base
        curr = list of strings with assets for market quote

        returns list of CoinPriceData
        """
        pass

    @abstractmethod
    def get_price_hist_marketchart(self, coindata: list[CoinData], currencies: list[str], date: str) -> list[CoinPriceData]:
        """Get history price of a coin or a token

        If chain = 'none' or None search for a coins otherwise search for token contracts

        coindata = list of CoinData or token contracts for market base
        curr = list of strings with assets for market quote
        date = historical date 

        returns list of CoinPriceData
        """
        pass

    def get_price_hist(self, coindata: list[CoinData], currencies: list[str], date: str) -> list[CoinPriceData]:
        """Get coingecko history price

        coindata = list of CoinData for market base
        curr = list of strings with assets for market quote
        date = historical date 

        returns list of CoinPriceData
        """
        return []

    def show_progress(self, nr: int, total: int):
        """Show progress to standard output
        """
        print(f'\rRetrieving nr {nr:3d} of {total}', end='', flush=True)
        #sys.stdout.write(f'Retrieving nr {nr:3d} of {total}\r')
        # sys.stdout.flush()

    def show_allowance(self, allowance):
        """Show allowance data to standard output on same row
        """
        allowance_str = json.dumps(allowance)[1:50]
        print('\r'+allowance_str.rjust(80), end='', flush=True)

    # def write_to_file(self, pricedata: list[CoinPriceData], output_csv: str, output_xls: str, suffix: str):
    #     """Write a dataframe to a csv file and/or excel file

    #     pricedata = list of CoinPriceData
    #     output_csv = base filename for csv output file
    #     output_xls = base filename for xlsx output file
    #     suffix = last part of filename

    #     filename CSV file = config.OUTPUT_PATH+output_csv+suffix.csv
    #     filename XLS file = config.OUTPUT_PATH+output_xls+suffix.xlsx
    #     """
    #     if pricedata == []:
    #         print('Empty pricedata list, nothing to save')
    #         return

    #     df = self._convert_pricedata_to_df(pricedata)

    #     suffix = re.sub(r'[:;,!@#$%^&*()]', '', suffix)
    #     outputpath = config.OUTPUT_PATH
    #     if outputpath != '':
    #         outputpath = outputpath + '\\'

    #     if output_csv is not None:
    #         filepath = Path('{outputpath}{output_csv}{suffix}.csv')
    #         filepath.parent.mkdir(parents=True, exist_ok=True)
    #         df.to_csv(filepath)
    #         print(f'File written: {filepath}')

    #     if output_xls is not None:
    #         # remove timezone, because excel cannot handle this
    #         df['date'] = helperfunc.remove_tz(df['date'])
    #         filepath = Path(f'{outputpath}{output_xls}{suffix}.xlsx')
    #         filepath.parent.mkdir(parents=True, exist_ok=True)
    #         df.to_excel(filepath)
    #         print(f'File written: {filepath}')

    # def print_coinpricedata(self, pricedata: list[CoinPriceData]) -> None:
    #     """Print price data to output

    #     pricedata = list of CoinPriceData
    #     """
    #     if pricedata == []:
    #         print('Empty pricedata list, nothing to print')
    #         return

    #     # init pandas displaying
    #     pd.set_option('display.max_rows', None)
    #     pd.set_option('display.max_columns', None)
    #     pd.set_option('display.max_colwidth', 25)
    #     pd.set_option('display.float_format', '{:.6e}'.format)

    #     df = self._convert_pricedata_to_df(pricedata)
    #     print(df)
    #     print()

    # def _convert_pricedata_to_df(self, pricedata: list[CoinPriceData]) -> pd.DataFrame:
    #     """Converts list of objects to a pandas DataFrame

    #     json_normalize is used this way to flatten the coindata object inside the pricedata

    #     coindata = list of CoinPriceData

    #     returns pandas DataFrame
    #     """
    #     df = pd.json_normalize(data=[asdict(obj) for obj in pricedata])
    #     df.sort_values(by=['coin.name', 'curr'],
    #                    key=lambda col: col.str.lower(), inplace=True)
    #     return df


# def add_standard_arguments(exchange: str = '') -> ArgumentParser:
#     """Add default arguments

#     Only used in standalone running from command prompt
#     """
#     if exchange != '':
#         exchange = f' on {exchange}'

#     argparser = ArgumentParser()
#     argparser.add_argument('-d', '--date', type=str,
#                            help=f'Historical date to search{exchange}, format: 2011-11-04T00:05:23+04:00',
#                            default='2022-05-01T23:00')
#     argparser.add_argument('-c', '--coin', type=str,
#                            help=f'List of coins to search{exchange}', required=False)
#     argparser.add_argument('-oc', '--output_csv', type=str,
#                            help='Filename and path to output CSV file', required=False)
#     argparser.add_argument('-ox', '--output_xls', type=str,
#                            help='Filename and path to the output Excel file', required=False)
#     return argparser
