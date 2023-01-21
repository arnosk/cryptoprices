"""
Created on December 26, 2022

@author: arno

Command editor UI for searching coins on website / exchanges

"""
import shlex
import sys
from dataclasses import asdict
from typing import Protocol

import pandas as pd

from CoinData import CoinData, CoinSearchData
from CoinViewData import Command, DbResultStatus, SearchFunction


class SearchController(Protocol):
    def get_website(self) -> str:
        ...

    def search_website(self, searchstr: str) -> list[CoinSearchData]:
        ...

    def search_db(self, searchstr: str) -> list[CoinData]:
        ...

    def delete_coin(self, coin: CoinData) -> DbResultStatus:
        ...

    def insert_coin(self, coin: CoinSearchData) -> DbResultStatus:
        ...


class CoinSearchViewCli:
    """UI class for searching in command editor
    """

    def __init__(self) -> None:
        self.last_fn: SearchFunction = SearchFunction.NONE

    def delete_coin(self,  control: SearchController, coin: CoinData) -> None:
        """Try deleting coin via controller and show result
        """
        result = control.delete_coin(coin)
        match result:
            case DbResultStatus.NO_DATABASE:
                print('No database connection')
            case DbResultStatus.NO_TABLE:
                print('Table not found')
            case DbResultStatus.COIN_NOT_EXISTS:
                print(f'Coin {coin.name} not found in db')
            case DbResultStatus.DELETE_ERROR:
                print(f'Error deleting {coin.name} from database')
            case DbResultStatus.DELETE_OK:
                print(f'{coin.name} deleted from database')

    def insert_coin(self,  control: SearchController, coin: CoinSearchData) -> None:
        """Try inserting coin via controller and show result
        """
        result = control.insert_coin(coin)
        match result:
            case DbResultStatus.NO_DATABASE:
                print('No database connection')
            case DbResultStatus.COIN_EXISTS:
                print(
                    f'Database already has a row with the coin {coin.coin.name}')
            case DbResultStatus.INSERT_ERROR:
                print(f'Error adding {coin.coin.name} to database')
            case DbResultStatus.INSERT_OK:
                print(f'{coin.coin.name} added to the database')

    def print_items(self, items: list, heading_text: str, col_drop=[]):
        """Print search result to terminal
        """
        # init pandas displaying
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_colwidth', 20)
        pd.set_option('display.float_format', '{:.6e}'.format)

        if (len(items) > 0):
            df = pd.json_normalize(data=[asdict(obj) for obj in items])
            #itemsdf = pd.DataFrame(items)
            df = df.drop(
                ['route', 'image_thumb', 'image_large'], axis=1, errors='ignore')
            if col_drop != []:
                df = df.drop(col_drop, axis=1, errors='ignore')
            print(f'Search from {heading_text}')
            print(df)
        else:
            print(f'Coin not found from {heading_text}')

    def ui_delete(self, control: SearchController) -> list[CoinData]:
        """UI for delete a coin
        """
        print(f'Search database for deletion')
        searchstr = input('Search for coin: ')
        return self.search_db(control, searchstr)

    def ui_search(self, control: SearchController) -> list[CoinSearchData]:
        """UI for input search string
        """
        print(f'New search on {control.get_website()}')
        searchstr = input('Search for coin: ')
        self.search_db(control, searchstr)
        return self.search_website(control, searchstr)

    def search_db(self, control: SearchController, searchstr: str) -> list[CoinData]:
        # Show result from search in databes database
        result = control.search_db(searchstr)
        self.print_items(result, 'Database')
        return result

    def search_website(self, control: SearchController, searchstr: str) -> list[CoinSearchData]:
        # Do search on website / exchange assets
        result = control.search_website(searchstr)
        self.print_items(result, control.get_website())
        return result

    def get_main_input_command(self, max_row: int) -> Command:
        """ The main user input
        """
        message = '(N)ew search, (D)elete or (Q)uit: '
        if max_row >= 0:
            message = f'Select row nr for {self.last_fn.value}, or {message}'

        input_str = input(message)
        if input_str == '':
            input_str = 'new'
        command, *arguments = shlex.split(input_str)
        return Command(command, arguments)

    def ui_root(self, control: SearchController) -> None:
        """Root UI for searching

        New search on exchange
        Quit exits the program
        After search select row to insert coin into the table, if it doesn't already exists
        """
        print(f'Searching assets on {control.get_website()}')
        coinsearchdata: list[CoinSearchData] = []
        coindeletedata: list[CoinData] = []
        while True:
            match self.last_fn:
                case SearchFunction.INSERT:
                    maximum = len(coinsearchdata) - 1
                case SearchFunction.DELETE:
                    maximum = len(coindeletedata) - 1
                case _:
                    maximum = 0
            cmd = self.get_main_input_command(maximum)

            match cmd:
                case Command(command='new' | 'n'):
                    coinsearchdata = self.ui_search(control)
                    self.last_fn = SearchFunction.INSERT
                case Command(command='delete' | 'd'):
                    coindeletedata = self.ui_delete(control)
                    self.last_fn = SearchFunction.DELETE
                case Command(command='quit' | 'q' | 'exit' | 'e', arguments=['--force' | '-f', *rest]):
                    print("Sending SIGTERM to all processes and quitting the program.")
                    sys.exit('Exiting')
                case Command(command='quit' | 'q' | 'exit' | 'e'):
                    sys.exit('Exiting')
                case _:
                    try:
                        value = int(cmd.command)
                    except ValueError:
                        print(f'Unknown command {cmd.command!r}.')
                    else:
                        if (value >= 0 and value <= maximum):
                            match self.last_fn:
                                case SearchFunction.INSERT:
                                    self.insert_coin(
                                        control, coinsearchdata[value])
                                case SearchFunction.DELETE:
                                    self.delete_coin(
                                        control, coindeletedata[value])
                                case _:
                                    print('No row to select! Try again.')
                        else:
                            print('No correct row number! Try again.')
