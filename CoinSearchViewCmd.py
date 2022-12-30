"""
Created on December 26, 2022

@author: arno

Command editor UI for searching coins on website / exchanges

"""
import shlex
import sys
from dataclasses import asdict, dataclass

import pandas as pd

import config
import DbHelper
from CoinData import CoinSearchData
from CoinSearch import CoinSearch
from Db import Db
from DbHelper import DbTableName


@dataclass
class Command:
    """Class that represents a command."""

    command: str
    arguments: list[str]

    def __post_init__(self):
        self.command = self.command.lower()
        self.arguments = [x.lower() for x in self.arguments]


class CoinSearchViewCmd:
    """UI class for searching in command editor
    """

    def insert_coin_check(self, db: Db, cs: CoinSearch, coin: CoinSearchData):
        """Check for existence of selected coin before inserting coin in database

        The selected row is inserted into the table, if it doesn't already exists

        db = instance of Db
        coin = search data with retrieved coin info from web
        """
        coin_id = coin.coin.siteid
        coin_name = coin.coin.name

        # check if coin name, symbol is already in our database
        if db.has_connection():
            # if table doesn't exist, create table coins
            if not db.check_table(DbTableName.coin.name):
                DbHelper.create_coin_table(db)

            website_id = cs.handle_website_id(db)

            db_result = DbHelper.get_coin(db, coin_id, website_id)
            if len(db_result):
                print(f'Database already has a row with the coin {coin_name}')
            else:
                # add new row to table coins
                insert_result = DbHelper.insert_coin(db, coin.coin, website_id)
                if insert_result > 0:
                    print(f'{coin_name} added to the database')

                    # safe coin images
                    images_urls = {'thumb': coin.image_thumb,
                                   'large': coin.image_large}
                    cs.save_images(images_urls, coin_name)
                else:
                    print(f'Error adding {coin_name} to database')
        else:
            print('No database connection')

    def print_search_result(self, items: list, text: str, col_drop=[]):
        """Print search result to terminal

        items = list of items to be printed on screen
        text = heading above the printed results
        col_drop = list with columns names not to be shown
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
            print('Search from', text)
            print(df)
        else:
            print('Coin not found from', text)

    def ui_search(self, db: Db, cs: CoinSearch) -> list[CoinSearchData]:
        """UI for input search string
        """
        print('New search')
        searchstr = input('Search for coin: ')

        # Show result from search in databes database
        db_result = cs.search_id_db(db, searchstr)
        self.print_search_result(db_result, 'Database')

        # Do search on website / exchange assets
        cs_result = cs.search(searchstr)
        self.print_search_result(cs_result, cs.website)

        return cs_result

    def get_main_input_command(self, max_row: int) -> Command:
        """ The main user input
        """
        if max_row <= 0:
            message = '(N)ew search, or (Q)uit'
        else:
            message = 'Select row nr for coin to store in database, or (N)ew search, or (Q)uit'

        command, *arguments = shlex.split(input(message))
        return Command(command, arguments)

    def ui_root(self, db: Db, cs: CoinSearch):
        """Root UI for searching and stopping

        New search on exchange
        Quit exits the program
        After search select row to insert coin into the table, if it doesn't already exists
        """
        coinsearchdata = []
        while True:
            maximum = len(coinsearchdata) - 1
            cmd = self.get_main_input_command(maximum)

            match cmd:
                case Command(command='new' | 'n'):
                    print('New search')
                    coinsearchdata = self.ui_search(db, cs)
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
                            self.insert_coin_check(
                                db, cs, coinsearchdata[value])
                        else:
                            print('No correct row number! Try again.')
