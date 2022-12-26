"""
Created on Mar 23, 2022

@author: arno

Collecting prices

Coingecko
"""
import copy
import math

from dateutil import parser

import config
import helperfunc
from CoinData import CoinData, CoinPriceData
from CoinPrice import CoinPrice
from DbHelper import DbWebsiteName


class CoinPriceCoingecko(CoinPrice):
    """Class for retrieving price data of a set of coins on the coingecko website
    """

    def __init__(self) -> None:
        self.website = DbWebsiteName.coingecko.name
        super().__init__()

    def get_price_current(self, coindata: list[CoinData], currencies: list[str]) -> list[CoinPriceData]:
        """Get coingecko current price

        coindata = list of CoinData for market base
        curr = list of strings with assets for market quote

        returns list of CoinPriceData
        """
        # convert list to comma-separated string
        coins = ','.join(coin.siteid for coin in coindata)
        curr = ','.join(currencies)

        # make parameters for api call
        params = {}
        params['ids'] = coins
        params['vs_currencies'] = curr
        params['include_last_updated_at'] = True

        url = f'{config.COINGECKO_URL}/simple/price'
        url = self.req.api_url_params(url, params)
        resp = self.req.get_request_response(url)

        # create list of CoinPriceData from respone
        prices: list[CoinPriceData] = []
        for resp_key, resp_val in resp.items():
            for coin in coindata:
                if resp_key == coin.siteid:
                    date = helperfunc.convert_timestamp(
                        resp_val['last_updated_at'])
                    for currency in currencies:
                        if currency in resp_val:
                            prices.append(CoinPriceData(
                                date=date,
                                coin=coin,
                                curr=currency,
                                price=resp_val[currency]))

        return prices

    def get_price_current_token(self, coindata: list[CoinData], currencies: list[str]) -> list[CoinPriceData]:
        """Get coingecko current price of a token

        coindata = list of CoinData for market base
        curr = list of strings with assets for market quote

        returns list of CoinPriceData

        coindata.chain = chain where contracts are
        coindata.siteid = contract address
        """
        # convert list to comma-separated string
        curr = ','.join(currencies)
        chains = [coin.chain for coin in coindata]

        # prepare parameters for api call
        params = {}
        params['vs_currencies'] = curr
        params['include_last_updated_at'] = True

        # create empty list of CoinPriceData from respone
        prices: list[CoinPriceData] = []

        # make api call per chain
        for chain in chains:
            # convert list to comma-separated string
            contracts = ','.join(
                coin.siteid for coin in coindata if coin.chain == chain)

            # prepare parameters for api call
            params['contract_addresses'] = contracts

            url = f'{config.COINGECKO_URL}/simple/token_price/{chain}'
            url = self.req.api_url_params(url, params)
            resp = self.req.get_request_response(url)

            # remove status_code from dictionary
            resp.pop('status_code')

            # extend list of CoinPriceData from respone
            for resp_key, resp_val in resp.items():
                for coin in coindata:
                    if resp_key == coin.siteid:
                        date = helperfunc.convert_timestamp(
                            resp_val['last_updated_at'])
                        for currency in currencies:
                            if currency in resp_val:
                                prices.append(CoinPriceData(
                                    date=date,
                                    coin=coin,
                                    curr=currency,
                                    price=resp_val[currency]))

        return prices

    def get_price_hist(self, coindata: list[CoinData], currencies: list[str], date: str) -> list[CoinPriceData]:
        """Get coingecko history price

        coindata = list of CoinData for market base
        curr = list of strings with assets for market quote
        date = historical date 

        returns list of CoinPriceData
        """
        # set date in correct format for url call
        dt = parser.parse(date)
        date = dt.strftime('%d-%m-%Y_%H:%M')

        prices: list[CoinPriceData] = []
        i = 0
        for coin in coindata:
            i += 1
            self.show_progress(i, len(coindata))
            url = f'{config.COINGECKO_URL}/coins/{coin.siteid}/history?date={date}&localization=false'
            resp = self.req.get_request_response(url)

            if resp['status_code'] == 'error':
                # got no status from request, must be an error
                for currency in currencies:
                    prices.append(CoinPriceData(
                        date=dt,
                        coin=coin,
                        curr=currency,
                        price=math.nan,
                        volume=math.nan,
                        error=resp['error']))
            else:
                for currency in currencies:
                    # default values when not found in response
                    price = math.nan
                    volume = math.nan
                    error = 'no data found'

                    # get data from respones
                    if 'market_data' in resp:
                        if currency in resp['market_data']['current_price']:
                            price = resp['market_data']['current_price'][currency]
                            volume = resp['market_data']['total_volume'][currency]
                            error = ''

                    # add CoinPriceData
                    prices.append(CoinPriceData(
                        date=dt,
                        coin=coin,
                        curr=currency,
                        price=price,
                        volume=volume,
                        error=error))

        return prices

    def get_price_hist_marketchart(self, coindata: list[CoinData], currencies: list[str], date: str) -> list[CoinPriceData]:
        """Get coingecko history price of a coin or a token

        If chain = 'none' or None search for a coins otherwise search for token contracts

        chain = chain where contracts are or None for coins search
        coindata = list of CoinData or token contracts for market base
        curr = list of strings with assets for market quote
        date = historical date 

        returns list of CoinPriceData
        """
        # convert date to unix timestamp
        dt = parser.parse(date)  # local time
        ts = int(dt.timestamp())

        # make parameters
        params = {}
        params['from'] = ts
        params['to'] = ts

        prices: list[CoinPriceData] = []
        i = 0
        for coin in coindata:
            i += 1
            self.show_progress(i, len(coindata))

            for currency in currencies:
                params['vs_currency'] = currency

                coinprice = self.get_pricedata_hist_marketchart_retry(
                    coin, dt, ts, params, currency)
                prices.append(coinprice)

        return prices

    def get_pricedata_hist_marketchart_retry(self, coin: CoinData, dt, ts, params, currency) -> CoinPriceData:
        """Get history price data for one coin from and to specific date

        with retry mechanism for bigger time range when no data is found
        increase time range until data is found

        coindata = CoinData for market base and quote and chain
        date = historical date 

        return CoinPriceData
        """
        params_try = copy.deepcopy(params)

        if (coin.chain == '' or coin.chain == 'none' or coin.chain is None):
            url = f'{config.COINGECKO_URL}/coins/{coin.siteid}/market_chart/range'
        else:
            url = f'{config.COINGECKO_URL}/coins/{coin.chain}/contract/{coin.siteid}/market_chart/range'

        date = dt
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
                resp_prices = resp['prices']
                if len(resp_prices) > 0:
                    # select result with timestamp nearest to desired date ts
                    resp_price_index = self.search_price_minimal_timediff(
                        resp_prices, ts, True)

                    # set found coin price data
                    date = helperfunc.convert_timestamp(
                        resp_prices[resp_price_index][0], True)
                    price = resp_prices[resp_price_index][1]
                    volume = resp['total_volumes'][resp_price_index][1]
                    error = ''
                    break

        return CoinPriceData(date=date, coin=coin, curr=currency, price=price, volume=volume, error=error)

    def search_price_minimal_timediff(self, prices, ts: int, ms: bool = False) -> int:
        """Search for record in price data with the smallest time difference

        prices = results from request with price data
        ts = timestamp in sec if ms = False
        ts = timestamp in msec if ms = True

        result = index of record with smallest time difference with ts
        """
        timediff_minimal = 10**20
        price_index = 0
        index = 0
        ts = ts*1000 if ms == True else ts
        for price in prices:
            timediff = abs(ts - price[0])
            if timediff < timediff_minimal:
                timediff_minimal = timediff
                price_index = index
            index += 1
        return price_index
