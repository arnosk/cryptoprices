"""
@author: Arno
@created: 2022-10-13
@modified: 2023-05-20

Base Class CoinSearch

"""
from abc import ABC, abstractmethod
from enum import Enum, auto

import src.db.DbHelper as DbHelper
from src.data.CoinData import CoinData, CoinSearchData
from src.db.Db import Db
from src.req.RequestHelper import RequestHelper


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
        self.search_method: SearchMethod

    @abstractmethod
    def search(self, coin_search: str) -> list[CoinSearchData]:
        """Searching coins on exchange
        """
        pass

    def save_images(self, image_urls: dict, coin_name: str):
        """Save image files for one coin
        """
        pass

    def set_search_method(self, search_method: SearchMethod) -> None:
        pass

    # todo: move to other class or fn for db interface...

    def search_db(self, db: Db, search: str) -> list[CoinData]:
        """Search for coin in database
        """
        coindata = []
        if DbHelper.check_coin_table(db):
            self.website_id = self.get_website_id(db)
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
