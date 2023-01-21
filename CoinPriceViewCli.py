"""
Created on December 26, 2022

@author: arno

Command editor UI for get prices of coins on website / exchanges

"""
import json
import re
import shlex
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Protocol

import pandas as pd

import config
import helperfunc
from CoinData import CoinData, CoinPriceData
from CoinViewData import Command, OutputFileType, PriceFunction


class PriceController(Protocol):
    def get_website(self) -> str:
        ...

    def get_price_current(self) -> list[CoinPriceData]:
        ...

    def get_price_hist(self, date: str) -> list[CoinPriceData]:
        ...

    def get_price_hist_marketchart(self, date: str) -> list[CoinPriceData]:
        ...

    def set_currency_data(self, currency_data: list[str]) -> None:
        ...

    def set_coin_data(self, coin_data: list[CoinData]) -> None:
        ...

    def load_coin_data_db(self) -> None:
        ...


class CoinPriceViewCli:
    """UI class for getting prices in command editor
    """

    def __init__(self) -> None:
        self.price_data: list[CoinPriceData] = []
        self.last_date: str
        self.last_fn: PriceFunction
        self.chain: str = ''

    def update_progress(self, nr: int, total: int) -> None:
        """Show progress to standard output
        """
        print(f'\rRetrieving nr {nr:3d} of {total}', end='', flush=True)
        #sys.stdout.write(f'Retrieving nr {nr:3d} of {total}\r')
        # sys.stdout.flush()

    def update_progress_text(self, text: str) -> None:
        """Show progress text on same row
        """
        text = json.dumps(text)[1:50]
        print('\r'+text.rjust(80), end='', flush=True)

    def update_waiting_time(self, time: int) -> None:
        """Show waiting time
        """
        print(f'\rWaiting for retry, {time:3d} seconds remaining.',
              end='', flush=True)

    def write_to_file(self, control: PriceController, pricedata: list[CoinPriceData], filetype: OutputFileType) -> None:
        """Write a dataframe to a csv file and/or excel file

        filename = config.OUTPUT_PATH+websitename+method+date.filetype
        """
        if pricedata == []:
            print('Empty pricedata list, nothing to save')
            return

        df = self._convert_pricedata_to_df(pricedata)

        outputpath = config.OUTPUT_PATH
        if outputpath != '':
            outputpath = f'{outputpath}\\'

        website = control.get_website()
        file_str = f'{outputpath}{website}_{self.last_fn.value}_{self.last_date}.{filetype.name.lower()}'
        file_str = re.sub(r'[:;,!@#$%^&*()]', '', file_str)
        filepath = Path(file_str)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        if filetype == OutputFileType.CSV:
            df.to_csv(filepath)

        if filetype == OutputFileType.XLSX:
            # remove timezone, because excel cannot handle this
            df['date'] = helperfunc.remove_tz(df['date'])
            df.to_excel(filepath)

        print(f'File written: {filepath}')

    def print_coinpricedata(self, message: str, pricedata: list[CoinPriceData]) -> None:
        """Print price data to output
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
        print(f'{message}, {self.last_fn.value}, {self.last_date}')
        print(df)
        print()

    def _convert_pricedata_to_df(self, pricedata: list[CoinPriceData]) -> pd.DataFrame:
        """Converts list of objects to a pandas DataFrame

        json_normalize is used this way to flatten the coindata object inside the pricedata
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

    def show_help(self) -> None:
        """Show the available cli help commands
        """
        print('Available commands: ')
        print('Help - this help screen')
        print('(Q)uit - exit this program')
        print('(N)ow - get current prices')
        print('(H)ist date - get historical prices via market chart, when no date, the default date is taken')
        print('H2 date or hist2 date - get historical prices (only CoinGecko), when no date, the default date is taken')
        print('DB - use coins defined in database (default)')
        print('(C)oin coin_id - use the coin id (can be multiple)')
        print('Curr currency_id - use the currency id (can be multiple), defaults to btc,eth,eur,usd')
        print('Chain chain_id - change chain, only used for Alcor website')
        print('XLS - Write the retrieved data to an xls-file')
        print('CSV - Write the retrieved data to an csv-file')
        print(
            '(A)uto date [filetype] - do all types and write to xls or csv, defaults to both')
        print()

    def price_current(self, control: PriceController) -> None:
        """Show current prices
        """
        self.price_data = control.get_price_current()
        self.last_date = helperfunc.convert_date_to_utc_str(datetime.now())
        self.last_fn = PriceFunction.CURRENT
        self.print_coinpricedata(f'* Current price of coins',
                                 self.price_data)

    def price_hist(self, control: PriceController, date: str) -> None:
        """Show historical prices via simple method
        """
        self.last_date = date
        self.last_fn = PriceFunction.HISTORICAL_SIMPLE
        self.price_data = control.get_price_hist(self.last_date)
        self.print_coinpricedata('* History price of coins',
                                 self.price_data)

    def price_hist_marketchart(self, control: PriceController, date: str) -> None:
        """Show historical prices via marketchart
        """
        self.last_date = date
        self.last_fn = PriceFunction.HISTORICAL_MARKETCHART
        self.price_data = control.get_price_hist_marketchart(
            self.last_date)
        self.print_coinpricedata('* History price of coins via marketchart',
                                 self.price_data)

    def str_to_list(self, data: str) -> list[str]:
        """Make a list of string of values
        """
        return re.split('[;,]', data)

    def str_to_coindata(self, data: str) -> list[CoinData]:
        """Make a list of string of values
        """
        coins = re.split('[;,]', data)
        coin_data = [CoinData(siteid=i, chain=self.chain, symbol=i)
                     for i in coins]
        return coin_data

    def get_main_input_command(self) -> Command:
        """ The main user input
        """
        message = 'Command, help, or (Q)uit : '
        print()
        input_str = input(message)
        if input_str == '':
            input_str = 'help'
        command, *arguments = shlex.split(input_str)
        return Command(command, arguments)

    def ui_root(self, control: PriceController, date: str) -> None:
        """CLI UI main program:
        """
        print(f'Show price of assets on {control.get_website()}')
        while True:
            cmd = self.get_main_input_command()

            match cmd:
                case Command(command='quit' | 'q' | 'exit' | 'e'):
                    sys.exit('Exiting')
                case Command(command='help'):
                    self.show_help()
                case Command(command='now' | 'n'):
                    self.price_current(control)
                case Command(command='hist2' | 'h2', arguments=[rest]):
                    date = rest
                    self.price_hist(control, date)
                case Command(command='hist2' | 'h2'):
                    self.price_hist(control, date)
                case Command(command='hist' | 'h', arguments=[rest]):
                    date = rest
                    self.price_hist_marketchart(control, date)
                case Command(command='hist' | 'h'):
                    self.price_hist_marketchart(control, date)
                case Command(command='db'):
                    control.load_coin_data_db()
                case Command(command='coin' | 'c', arguments=[rest]):
                    coin_data = self.str_to_coindata(rest)
                    control.set_coin_data(coin_data)
                case Command(command='curr' | 'currency' | 'currencies', arguments=[rest]):
                    curr_data = self.str_to_list(rest)
                    control.set_currency_data(curr_data)
                case Command(command='chain', arguments=[rest]):
                    self.chain = re.sub(r'[:;,!@#$%^&*()]', '', rest)
                    print(f'New chain set to: {self.chain}')
                case Command(command='xls'):
                    self.write_to_file(control, self.price_data,
                                       OutputFileType.XLSX)
                case Command(command='csv'):
                    self.write_to_file(control, self.price_data,
                                       OutputFileType.CSV)
                case Command(command='a' | 'auto' | 'all', arguments=['xls' | 'csv' | 'both', *rest]):
                    pass
                case _:
                    print(f'Unknown command {cmd.command!r}, try again.')
