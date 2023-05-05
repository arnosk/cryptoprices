"""
Created on October 15, 2022

@author: arno

Base Class CoinPrice

"""
from abc import ABC, abstractmethod
from typing import Callable

from src.data.CoinData import CoinData, CoinPriceData
from src.req.RequestHelper import RequestHelper


class CoinPrice(ABC):
    """Base class for looking up the price of a coin on an exchange or provider
    """
    website: str

    def __init__(self) -> None:
        self.website_id: int = 0
        self.req = RequestHelper()
        self.nr_try_max: int = 10
        self.view_update_progress: Callable[[int, int], None]
        self.view_update_progress_text: Callable[[str], None]

    @abstractmethod
    def get_price_current(self, coindata: list[CoinData], currencies: list[str]) -> list[CoinPriceData]:
        """Get current price

        coindata = list of CoinData for market base
        curr = list of strings with assets for market quote

        returns list of CoinPriceData
        """
        pass

    @abstractmethod
    def get_price_hist_marketchart(self, coindata: list[CoinData], currencies: list[str], date: str) -> list[CoinPriceData]:
        """Get history price of a coin or a token

        If chain = 'none' or None search for a coins otherwise search for token contracts

        coindata = list of CoinData or token contracts for market base
        curr = list of strings with assets for market quote
        date = historical date 

        returns list of CoinPriceData
        """
        pass

    def get_price_hist(self, coindata: list[CoinData], currencies: list[str], date: str) -> list[CoinPriceData]:
        """Get coingecko history price

        coindata = list of CoinData for market base
        curr = list of strings with assets for market quote
        date = historical date 

        returns list of CoinPriceData
        """
        return []

    def attach_view_update_progress(self, fn_progress: Callable[[int, int], None]) -> None:
        """Set the viewers update progress function to the coinprice program
        """
        self.view_update_progress = fn_progress

    def attach_view_update_progress_text(self, fn_progress_text: Callable[[str], None]) -> None:
        """Set the viewers update progress text function to the coinprice program
        """
        self.view_update_progress_text = fn_progress_text

    def attach_view_update_waiting_time(self, fn_waiting_time: Callable[[int], None]) -> None:
        """Set the viewers waiting time function to the coinprice program
        """
        self.req.attach_view_update_waiting_time(fn_waiting_time)

    # def show_progress(self, nr: int, total: int):
    #     """Show progress to standard output
    #     """
    #     print(f'\rRetrieving nr {nr:3d} of {total}', end='', flush=True)
    #     #sys.stdout.write(f'Retrieving nr {nr:3d} of {total}\r')
    #     # sys.stdout.flush()

    # def show_allowance(self, allowance):
    #     """Show allowance data to standard output on same row
    #     """
    #     allowance_str = json.dumps(allowance)[1:50]
    #     print('\r'+allowance_str.rjust(80), end='', flush=True)
