"""
Created on December 26, 2022

@author: arno

Command editor UI for searching coins on website / exchanges

"""
import shlex
import sys
from dataclasses import asdict, dataclass
from typing import Protocol

import pandas as pd

from CoinData import CoinData, CoinSearchData


class Controller(Protocol):
    def get_website(self) -> str:
        ...

    def search_website(self, searchstr: str) -> list[CoinSearchData]:
        ...

    def search_db(self, searchstr: str) -> list[CoinData]:
        ...

    def insert_coin_check(self, coin: CoinSearchData):
        ...


@dataclass
class Command:
    """Class that represents a command for CLI view"""

    command: str
    arguments: list[str]

    def __post_init__(self):
        self.command = self.command.lower()
        self.arguments = [x.lower() for x in self.arguments]


class CoinSearchViewCmd:
    """UI class for searching in command editor
    """

    def show_insert_coin_result(self, text: str) -> None:
        """Show the result after chosing a coin for inserting
        """
        print(f'{text}')

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
            print('Search from', heading_text)
            print(df)
        else:
            print('Coin not found from', heading_text)

    def ui_search(self, control: Controller) -> list[CoinSearchData]:
        """UI for input search string
        """
        print('New search')
        searchstr = input('Search for coin: ')

        # Show result from search in databes database
        db_result = control.search_db(searchstr)
        self.print_items(db_result, 'Database')

        # Do search on website / exchange assets
        cs_result = control.search_website(searchstr)
        self.print_items(cs_result, control.get_website())

        return cs_result

    def get_main_input_command(self, max_row: int) -> Command:
        """ The main user input
        """
        if max_row < 0:
            message = '(N)ew search, or (Q)uit : '
        else:
            message = 'Select row nr for coin to store in database, or (N)ew search, or (Q)uit : '

        input_str = input(message)
        if input_str == '':
            input_str = 'new'
        command, *arguments = shlex.split(input_str)
        return Command(command, arguments)

    def ui_root(self, control: Controller) -> None:
        """Root UI for searching and stopping

        New search on exchange
        Quit exits the program
        After search select row to insert coin into the table, if it doesn't already exists
        """
        print(f'Searching assets on {control.get_website()}')
        coinsearchdata = []
        while True:
            maximum = len(coinsearchdata) - 1
            cmd = self.get_main_input_command(maximum)

            match cmd:
                case Command(command='new' | 'n'):
                    coinsearchdata = self.ui_search(control)
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
                            control.insert_coin_check(coinsearchdata[value])
                        else:
                            print('No correct row number! Try again.')
