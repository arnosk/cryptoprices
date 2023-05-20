"""
@author: Arno
@created: 2022-12-29
@modified: 2023-05-20

Controller part for get prices of coins on website / exchanges

"""
import src.db.DbHelper as DbHelper
from src.data.CoinData import CoinData, CoinPriceData
from src.db.Db import Db
from src.models.CoinPrice import CoinPrice
from src.views.CoinPriceViewCli import CoinPriceViewCli


class CoinPriceController:
    """Controller for getting prices from crypto exchanges"""

    def __init__(self, view: CoinPriceViewCli, price_prg: CoinPrice, db: Db) -> None:
        self.view = view
        self.price_prg = price_prg
        self.db = db
        self.price_prg.attach_view_update_progress(self.view.update_progress)
        self.price_prg.attach_view_update_progress_text(self.view.update_progress_text)
        self.price_prg.attach_view_update_waiting_time(self.view.update_waiting_time)
        self.price_prg.website_id = DbHelper.get_website_id(
            self.db, self.price_prg.website
        )
        self.coin_data: list[CoinData] = []
        self.currency_data: list[str] = ["usd", "eur", "btc", "eth"]

    def get_website(self) -> str:
        return self.price_prg.website

    def get_price_current(self) -> list[CoinPriceData]:
        """Get current price"""
        return self.price_prg.get_price_current(self.coin_data, self.currency_data)

    def get_price_hist(self, date: str) -> list[CoinPriceData]:
        """Get coingecko history price"""
        return self.price_prg.get_price_hist(self.coin_data, self.currency_data, date)

    def get_price_hist_marketchart(self, date: str) -> list[CoinPriceData]:
        """Get history price of a coin or a token"""
        return self.price_prg.get_price_hist_marketchart(
            self.coin_data, self.currency_data, date
        )

    def set_currency_data(self, currency_data: list[str]) -> None:
        """Set the currency data manual"""
        self.currency_data = currency_data

    def set_coin_data(self, coin_data: list[CoinData]) -> None:
        """Set the coin data manual"""
        self.coin_data = coin_data

    def load_coin_data_db(self) -> None:
        """Retrieve the coin data in database"""
        if self.price_prg.website_id > 0:
            coins = DbHelper.get_coins(self.db, "", self.price_prg.website_id)
            self.coin_data = [
                CoinData(siteid=i[0], name=i[1], symbol=i[2], chain=i[3], base=i[4])
                for i in coins
            ]

    def run(self, coin_data: list[CoinData], date: str):
        """For now:

        1: Get current prices
        2: Get historical prices
        """
        self.coin_data = coin_data
        self.view.ui_root(self, date)
