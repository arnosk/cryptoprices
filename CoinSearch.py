"""
Created on October 13, 2022

@author: arno

Base Class CoinSearch

"""
import shlex
import sys
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from enum import Enum, auto

import pandas as pd

import DbHelper
from CoinData import CoinData, CoinSearchData
from Db import Db
from DbHelper import DbTableName
from RequestHelper import RequestHelper


@dataclass
class Command:
    """Class that represents a command."""

    command: str
    arguments: list[str]

    def __post_init__(self):
        self.command = self.command.lower()
        self.arguments = [x.lower() for x in self.arguments]


class SearchMethod(Enum):
    """Class for enumerating search methods
    """
    assets = auto()
    web = auto()


class CoinSearch(ABC):
    """Base class for searching a coin on an exchange or provider
    """
    website: str

    def __init__(self) -> None:
        self.website_id: int = 0
        self.req = RequestHelper()

    @abstractmethod
    def search(self, db: Db, coin_search: str, assets: dict):
        """Searching coins on exchange

        Search coins in own database (if table exists)
        Show the results

        Search coins from exchange assets (already in assets)
        Show the results

        User can select a row number, from the table of search results
        To add that coin to the coins table, if it doesn't already exists

        db = instance of Db
        coin_search = string to search in assets
        assets = dictionary where each key is a chain with a list of string with assets from Alcor
        """
        pass

    def save_images(self, image_urls: dict, coin_name: str):
        """Save image files for one coin

        image_urls = dict if urls for images
        coin_name = string with name of coin
        """
        pass

    def search_id_db(self, db: Db, search: str) -> list[CoinData]:
        """Search for coin in database

        db = database
        search = coin name to be searched
        return value = list with search results
        """
        coindata = []
        if db.check_table(DbTableName.coin.name):
            self.website_id = DbHelper.get_website_id(db, self.website)
            if self.website_id > 0:
                db_result = DbHelper.get_coins(db, search, self.website_id)
                coindata = [CoinData(*x) for x in db_result]
        return coindata

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

    def insert_coin_check(self, db: Db, coin: CoinSearchData):
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
            if not db.check_table(DbTableName.website.name):
                DbHelper.create_coin_table(db)

            # check if new website / echange
            self.website_id = DbHelper.get_website_id(db, self.website)
            if self.website_id == 0:
                DbHelper.insert_website(db, self.website)
                self.website_id = DbHelper.get_website_id(db, self.website)

            db_result = DbHelper.get_coin(db, coin_id, self.website_id)
            if len(db_result):
                print(f'Database already has a row with the coin {coin_name}')
            else:
                # add new row to table coins
                insert_result = DbHelper.insert_coin(
                    db, coin.coin, self.website_id)
                if insert_result > 0:
                    print(f'{coin_name} added to the database')

                    # safe coin images
                    images_urls = {'thumb': coin.image_thumb,
                                   'large': coin.image_large}
                    self.save_images(images_urls, coin_name)
                else:
                    print(f'Error adding {coin_name} to database')
        else:
            print('No database connection')

    def input_coin_row(self, db: Db, coinsearch: list[CoinSearchData]):
        """UI for asking row number

        Handle user input after selecting coin

        New search, skips the function
        Quit exits the program
        Other the selected row is inserted into the table, if it doesn't already exists

        db = instance of Db
        user_input = char or integer with row number
        coinsearch = result from search

        """
        minimal = 0
        maximum = len(coinsearch) - 1
        message = 'Select coin to store in database, or (N)ew search, or (Q)uit'

        while True:
            # read a command with arguments from the input
            command, *arguments = shlex.split(input(f'{message} $ '))
            cmd = Command(command, arguments)

            match cmd:
                case Command(command='new' | 'n'):
                    print('New search')
                    break
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
                        if (value >= minimal and value <= maximum):
                            self.insert_coin_check(db, coinsearch[value])
                            break
                        else:
                            print('No correct row number! Try again.')
