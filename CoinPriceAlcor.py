"""
Created on Aug 31, 2022

@author: arno

Collecting prices

Alcor
"""
import copy
import math
from datetime import datetime

import config
import helperfunc
from CoinData import CoinData, CoinMarketData, CoinPriceData
from CoinPrice import CoinPrice
from DbHelper import DbWebsiteName


class CoinPriceAlcor(CoinPrice):
    """Class for retrieving price data of a set of coins on the Alcor website
    """

    def __init__(self) -> None:
        self.website = DbWebsiteName.ALCOR.name
        self.markets: dict[str, CoinMarketData] = {}
        super().__init__()

    def get_price_current(self, coindata: list[CoinData], currencies: list[str]) -> list[CoinPriceData]:
        """Get alcor current price
        """
        # make dict per chain (key1) with a dict of coins per coinid (key2)
        coin_srch: dict[str, dict[str, CoinData]] = {}
        for coin in coindata:
            coin_srch.setdefault(coin.chain, {}).update({coin.siteid: coin})

        # get all market data for each chain from Alcor site
        prices: list[CoinPriceData] = []
        for key_chain, val_coins in coin_srch.items():
            url = f'{config.ALCOR_URL.replace("?", key_chain)}/markets'
            resp = self.req.get_request_response(url)

            # search through result for coin in the dict
            for item in resp['result']:
                item_id = str(item['id'])
                if item_id in val_coins:
                    coin = val_coins[item_id]
                    coin.name = item['quote_token']['str']
                    coin.symbol = item['quote_token']['symbol']['name']
                    coin_price_data = CoinPriceData(
                        date=datetime.now(),
                        coin=coin,
                        curr=item['base_token']['str'],
                        price=item['last_price'],
                        volume=item['volume24'])
                    coin_market_data = CoinMarketData(
                        coin=coin,
                        curr=item['base_token']['str'])

                    prices.append(coin_price_data)
                    self.markets[coin.siteid] = coin_market_data

        return prices

    def get_price_hist_marketchart(self, coindata: list[CoinData], currencies: list[str], date: str) -> list[CoinPriceData]:
        """Get alcor history price of a coin via market chart data
        """
        # convert date to unix timestamp
        dt = helperfunc.convert_str_to_date(date)
        ts = int(dt.timestamp())

        # make parameters
        params = {}
        params['resolution'] = 60
        params['from'] = ts
        params['to'] = ts

        prices: list[CoinPriceData] = []
        i = 0
        for coin in coindata:
            i += 1
            self.view_update_progress(i, len(coindata))

            coinprice = self.get_pricedata_hist_marketchart_retry(
                coin, dt, ts, params)
            prices.append(coinprice)

        return prices

    def get_pricedata_hist_marketchart_retry(self, coin: CoinData, dt, ts, params) -> CoinPriceData:
        """Get history price data for one coin from and to specific date

        with retry mechanism for bigger time range when no data is found
        increase time range until data is found
        """
        params_try = copy.deepcopy(params)
        url = f'{config.ALCOR_URL.replace("?", coin.chain)}/markets/{coin.siteid}/charts'

        date = dt
        coin_base = self.markets[coin.siteid].curr
        price = math.nan
        volume = math.nan
        error = 'no data found'

        for nr_try in range(1, self.nr_try_max):
            # retry same coin with new date range
            params_try['from'] -= 2**(2*nr_try) * 3600
            params_try['to'] += 2**(2*nr_try) * 3600

            url_try = self.req.api_url_params(url, params_try)
            resp = self.req.get_request_response(url_try)

            # check for correct response
            if resp['status_code'] == 'error':
                # got no status from request, must be an error
                error = resp['error']
                break
            else:
                resp_prices = resp['result']
                if len(resp_prices) > 0:
                    # select result with timestamp nearest to desired date ts
                    resp_price_minimal = self.search_price_minimal_timediff(
                        resp_prices, ts, True)

                    # set found coin price data
                    date = helperfunc.convert_timestamp(
                        resp_price_minimal['time'], True)
                    price = resp_price_minimal['open']
                    volume = resp_price_minimal['volume']
                    error = ''
                    break

        return CoinPriceData(date=date, coin=coin, curr=coin_base, price=price, volume=volume, error=error)

    def search_price_minimal_timediff(self, prices, ts: int, ms: bool = False):
        """Search for record in price data with the smallest time difference

        ts = timestamp in sec if ms = False
        ts = timestamp in msec if ms = True
        """
        timediff_minimal = 10**20
        price_minimal = {}
        ts = ts*1000 if ms == True else ts
        for price in prices:
            timediff = abs(ts - price['time'])
            if timediff < timediff_minimal:
                timediff_minimal = timediff
                price_minimal = price
        return price_minimal
