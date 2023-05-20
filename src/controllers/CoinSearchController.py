"""
@author: Arno
@created: 2022-12-29
@modified: 2023-05-20

Controller part for searching crypto coins on website / exchanges

"""
import src.db.DbHelper as DbHelper
from src.data.CoinData import CoinData, CoinSearchData
from src.data.DbData import DbResultStatus
from src.db.Db import Db
from src.models.CoinSearch import CoinSearch, SearchMethod
from src.views.CoinSearchViewCli import CoinSearchViewCli


class CoinSearchController:
    """Controller for getting prices from crypto exchanges"""

    def __init__(self, view: CoinSearchViewCli, search_prg: CoinSearch, db: Db) -> None:
        self.view = view
        self.search_prg = search_prg
        self.db = db
        self.search_prg.website_id = DbHelper.get_website_id(
            self.db, self.search_prg.website
        )

    def run(self):
        self.view.ui_root(self)

    def get_website(self) -> str:
        return self.search_prg.website

    def search_website(self, searchstr: str) -> list[CoinSearchData]:
        return self.search_prg.search(searchstr)

    def search_db(self, searchstr: str) -> list[CoinData]:
        return self.search_prg.search_db(self.db, searchstr)

    def delete_coin(self, coin: CoinData) -> DbResultStatus:
        """Delete coin from database"""
        # check if coin name, symbol is already in our database
        if not self.db.has_connection():
            return DbResultStatus.NO_DATABASE

        # if table doesn't exist, create table coins
        if not DbHelper.check_coin_table(self.db):
            return DbResultStatus.NO_TABLE

        website_id = self.search_prg.get_website_id(self.db)

        db_result = DbHelper.get_coin(self.db, coin.siteid, website_id)
        if len(db_result) <= 0:
            return DbResultStatus.COIN_NOT_EXISTS

        # add new row to table coins
        result = DbHelper.delete_coin(self.db, coin.siteid, website_id)
        if result <= 0:
            return DbResultStatus.DELETE_ERROR

        return DbResultStatus.DELETE_OK

    def insert_coin(self, coin: CoinSearchData) -> DbResultStatus:
        """Insert coin in database

        The coin is inserted into the table, if it doesn't already exists
        """
        # check if coin name, symbol is already in our database
        if not self.db.has_connection():
            return DbResultStatus.NO_DATABASE

        # if table doesn't exist, create table coins
        if not DbHelper.check_coin_table(self.db):
            DbHelper.create_coin_table(self.db)

        website_id = self.search_prg.get_website_id(self.db)

        db_result = DbHelper.get_coin(self.db, coin.coin.siteid, website_id)
        if len(db_result):
            return DbResultStatus.COIN_EXISTS

        # add new row to table coins
        result = DbHelper.insert_coin(self.db, coin.coin, website_id)
        if result <= 0:
            return DbResultStatus.INSERT_ERROR

        # safe coin images
        images_urls = {"thumb": coin.image_thumb, "large": coin.image_large}
        self.search_prg.save_images(images_urls, coin.coin.name)
        return DbResultStatus.INSERT_OK

    def toggle_search_method(self) -> None:
        """Change the search method
        In case the search program has multiple (Coingecko)
        """
        if self.search_prg.search_method == SearchMethod.WEB:
            self.search_prg.set_search_method(SearchMethod.ASSETS)
        else:
            self.search_prg.set_search_method(SearchMethod.WEB)

    def get_search_method(self) -> SearchMethod:
        return self.search_prg.search_method
