"""
Created on December 26, 2022

@author: arno

Command editor UI for get prices of coins on website / exchanges

"""
import json
import re
from dataclasses import asdict
from pathlib import Path

import pandas as pd

import config
import helperfunc
from CoinData import CoinPriceData


class CoinPriceViewCmd:
    """UI class for getting prices in command editor
    """

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

    def update_progress(self, nr: int, total: int, message=None):
        self.show_progress(nr, total)
        if message != None:
            self.show_allowance(message)

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

    def print_coinpricedata(self, message: str, pricedata: list[CoinPriceData]) -> None:
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
        print()
        print(f'{message}')
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
