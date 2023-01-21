"""
Created on October 13, 2022

@author: arno

Base Class CoinSearch

"""
from abc import ABC, abstractmethod
from enum import Enum, auto

import DbHelper
from CoinData import CoinData, CoinSearchData
from Db import Db
from DbHelper import DbTableName
from RequestHelper import RequestHelper


class SearchMethod(Enum):
    """Class for enumerating search methods
    """
    ASSETS = auto()
    WEB = auto()


class CoinSearch(ABC):
    """Base class for searching a coin on an exchange or provider
    """
    website: str

    def __init__(self) -> None:
        self.website_id: int = 0
        self.req = RequestHelper()

    @abstractmethod
    def search(self, coin_search: str) -> list[CoinSearchData]:
        """Searching coins on exchange
        """
        pass

    def save_images(self, image_urls: dict, coin_name: str):
        """Save image files for one coin

        image_urls = dict if urls for images
        coin_name = string with name of coin
        """
        pass

    # todo: move to other class or fn for db interface...
    def search_id_db(self, db: Db, search: str) -> list[CoinData]:
        """Search for coin in database

        return value = list with search results
        """
        coindata = []
        if db.check_table(DbTableName.COIN.value):
            self.website_id = DbHelper.get_website_id(db, self.website)
            if self.website_id > 0:
                db_result = DbHelper.get_coins(db, search, self.website_id)
                coindata = [CoinData(*x) for x in db_result]
        return coindata

    def get_website_id(self, db: Db) -> int:
        """Get website id from memory or
        Get website id from database or
        insert row in website table
        """
        if self.website_id == 0:
            self.website_id = DbHelper.get_website_id(db, self.website)
            if self.website_id == 0:
                DbHelper.insert_website(db, self.website)
                self.website_id = DbHelper.get_website_id(db, self.website)
        return self.website_id
