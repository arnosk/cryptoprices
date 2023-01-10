"""
Created on Mar 23, 2022

@author: arno

Collecting prices

From Cryptowatch
"""
import copy
import math
import re
from datetime import datetime, timedelta
from typing import Callable

from dateutil import parser

import CoinPrice
import config
import helperfunc
from CoinData import CoinData, CoinMarketData, CoinPriceData
from CoinPrice import CoinPrice
from DbHelper import DbWebsiteName


class CoinPriceCryptowatch(CoinPrice):
    """Class for retrieving price data of a set of coins on the cryptowatch website
    """

    def __init__(self, strictness: int = 0, max_markets_per_pair: int = 0) -> None:
        self.website = DbWebsiteName.cryptowatch.name
        self.markets: list[CoinMarketData] = []
        self.id_coindata: int = 0
        self.strictness: int = strictness
        self.max_markets_per_pair: int = max_markets_per_pair
        super().__init__()

        # Update header of request session with user API key
        self.req.update_header({'X-CW-API-Key': config.CRYPTOWATCH_API})

    def get_price_current(self, coindata: list[CoinData], currencies: list[str], updateview: Callable) -> list[CoinPriceData]:
        """Get Cryptowatch current price
        """
        # check if markets are already loaded for all coindata
        if self.id_coindata != id(coindata):
            print('----------------loading market data--------------')
            self.markets = self.get_markets(
                coindata, currencies, self.strictness)
            self.id_coindata = id(coindata)

        prices: list[CoinPriceData] = []
        i = 0
        for market in self.markets:
            i += 1
            updateview(i, len(self.markets))

            if market.error == '':
                url_list = f'{market.route}/summary'
                resp = self.req.get_request_response(url_list)

                # check for correct result
                if resp['status_code'] == 'error':
                    # got no status from request, must be an error
                    prices.append(CoinPriceData(
                        date=datetime.now(),
                        coin=market.coin,
                        curr=market.curr,
                        exchange=market.exchange,
                        price=math.nan,
                        volume=math.nan,
                        active=market.active,
                        error=resp['error']))
                else:
                    prices.append(CoinPriceData(
                        date=datetime.now(),
                        coin=market.coin,
                        curr=market.curr,
                        exchange=market.exchange,
                        price=resp['result']['price']['last'],
                        volume=resp['result']['volume'],
                        active=market.active))

                if 'allowance' in resp:
                    allowance = resp['allowance']
                    updateview(i, len(self.markets), allowance)

        prices = self.filter_marketpair_on_volume(
            prices, self.max_markets_per_pair)
        return prices

    def get_price_hist_marketchart(self, coindata: list[CoinData], currencies: list[str], date: str, updateview: Callable) -> list[CoinPriceData]:
        """Get coingecko history price of a coin or a token
        """
        # check if markets are already loaded for all coindata
        if self.id_coindata != id(coindata):
            print('----------------loading market data--------------')
            self.markets = self.get_markets(
                coindata, currencies, self.strictness)
            self.id_coindata = id(coindata)

        # convert date to unix timestamp
        dt = helperfunc.convert_date_str(date)
        # api returns wrong date of 1 hour difference
        dt = dt + timedelta(hours=1)
        ts = int(dt.timestamp())

        # make parameters
        params = {}
        params['after'] = ts
        params['before'] = ts
        params['periods'] = 3600

        prices: list[CoinPriceData] = []
        i = 0
        for market in self.markets:
            i += 1
            updateview(i, len(self.markets))

            if market.error == '':
                coinprice = self.get_pricedata_hist_marketchart_retry(
                    market, dt, ts, params, updateview)
                prices.append(coinprice)

        prices = self.filter_marketpair_on_volume(
            prices, self.max_markets_per_pair)
        return prices

    def get_pricedata_hist_marketchart_retry(self, market: CoinMarketData, dt, ts, params, updateview: Callable) -> CoinPriceData:
        """Get history price data for one coin from and to specific date

        with retry mechanism for bigger time range when no data is found
        increase time range until data is found
        """
        params_try = copy.deepcopy(params)
        url = f'{market.route}/ohlc'

        date = dt
        coin = market.coin
        curr = market.curr
        exchange = market.exchange
        price = math.nan
        volume = math.nan
        active = market.active
        error = 'no data found'

        for nr_try in range(1, self.nr_try_max):
            # retry same coin with new date range
            params_try['after'] -= 2**(2*nr_try) * 3600
            params_try['before'] += 2**(2*nr_try) * 3600

            url_try = self.req.api_url_params(url, params_try)
            resp = self.req.get_request_response(url_try)

            # check for correct response
            if resp['status_code'] == 'error':
                # got no status from request, must be an error
                error = resp['error']
                break
            else:
                resp_prices = resp['result']['3600']
                if len(resp_prices) > 0:
                    # select result with timestamp nearest to desired date ts
                    resp_price_minimal = self.search_price_minimal_timediff(
                        resp_prices, ts, False)

                    # set found coin price data
                    date = helperfunc.convert_timestamp(
                        resp_price_minimal[0], False)
                    date = date + timedelta(hours=-1)  # api returns wrong date
                    price = resp_price_minimal[1]  # open
                    volume = resp_price_minimal[5]  # volume
                    error = ''
                    break

            if 'allowance' in resp:
                allowance = resp['allowance']
                updateview(1, len(self.markets), allowance)

        return CoinPriceData(date=date, coin=coin, curr=curr, exchange=exchange, price=price, volume=volume, active=active, error=error)

    def search_price_minimal_timediff(self, prices, ts: int, ms: bool = False):
        """Search for record in price data with the smallest time difference

        ts = timestamp in sec if ms = False
        ts = timestamp in msec if ms = True
        """
        timediff_minimal = 10**20
        price_minimal = []
        ts = ts*1000 if ms == True else ts
        for price in prices:
            timediff = abs(ts - price[0])
            if timediff < timediff_minimal:
                timediff_minimal = timediff
                price_minimal = price
        return price_minimal

    def filter_marketpair_on_volume(self, prices: list[CoinPriceData], max_markets_per_pair: int) -> list[CoinPriceData]:
        """Filter the price data with same market pair. 

        Only the exchanges with the greatest volume for a market pair will stay

        max_markets_per_pair = maximum rows of the same pair on different exchanges
                            when 0, no filtering will be done and all markets are shown
        """
        # do nothing
        if max_markets_per_pair <= 0 or len(prices) == 0:
            return prices

        # make new dictionary, with pair as key, list of price as value
        price_per_pair: dict[str, list[CoinPriceData]] = {}
        for price in prices:
            if price.volume > 0:
                pair = f'{price.coin.symbol}{price.curr}'
                if not pair in price_per_pair.keys():
                    price_per_pair[pair] = []
                price_per_pair[pair].append(price)

        # make new list of prices with max markets per pair
        new_prices: list[CoinPriceData] = []
        for val_prices in price_per_pair.values():
            # sort list of dictionaries of same pair on volume
            val_prices_sorted = sorted(val_prices,
                                       key=lambda d: d.volume,
                                       reverse=True)

            # get the first x price items
            for i in range(0, min(len(val_prices_sorted), max_markets_per_pair)):
                new_prices.append(val_prices_sorted[i])

        return new_prices

    def get_markets(self, coindata: list[CoinData], currencies: list[str], strictness=0) -> list[CoinMarketData]:
        """Get cryptowatch markets for chosen coins

        strictness = strictly (0), loose (1) or very loose (2) search for base
                    0: strictly is base exactly equals currency
                    1: loose is base contains currency with 1 extra char in front and/or at the end
                    2: very loose is base contains currency

        NOT Doing this anymore: if coin does not exist as base, try as quote
        """
        markets: list[CoinMarketData] = []
        for coin in coindata:
            url = f'{config.CRYPTOWATCH_URL}/assets/{coin.symbol}'
            resp = self.req.get_request_response(url)

            if resp['status_code'] == 200:
                resp_markets = resp['result']['markets']

                # check if base or quote exists in result
                if 'base' in resp_markets:
                    res = resp_markets['base']

                    # filter active pairs
                    res = list(filter(lambda r: r['active'] == True, res))

                    if strictness == 0:
                        # Strict/Exact filter only quote from currencies
                        res_filter = list(
                            filter(lambda r: r['pair'].replace(coin.symbol, '') in currencies, res))
                        # filter(lambda r: r['curr'] in currencies, res))

                        # check if markets are found, else don't filter
                        if len(res_filter) > 0:
                            res = res_filter

                    if strictness >= 1:
                        # Loose filter only quote from currencies
                        res_filter = []
                        for c in currencies:
                            if strictness == 1:
                                # Loose (quote can have 0 or 1 character before and/or after given currency)
                                res_curr = list(filter(lambda r: re.match(
                                    '^'+coin.symbol+'\\w?'+c+'\\w?$', r['pair']), res))
                            else:
                                # Very Loose (quote must contain given currency)
                                res_curr = list(
                                    filter(lambda r: c in r['pair'], res))
                            res_filter.extend(res_curr)
                        res = res_filter

                    for r in res:
                        markets.append(CoinMarketData(
                            coin=coin,
                            curr=r['pair'].replace(coin.symbol, ''),
                            exchange=r['exchange'],
                            active=r['active'],
                            pair=r['pair'],
                            route=r['route']))

                else:
                    markets.append(CoinMarketData(
                        coin=coin,
                        curr='not data found',
                        active=False,
                        error='not data found'))

            else:
                markets.append(CoinMarketData(
                    coin=coin,
                    curr='error',
                    active=False,
                    error=resp['error']))

        return markets
