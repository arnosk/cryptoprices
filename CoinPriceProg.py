"""
Created on December 29, 2022

@author: arno

Controller part for get prices of coins on website / exchanges

"""
import argparse
import re

import config
import src.db.DbHelper as DbHelper
from src.controllers.CoinPriceController import CoinPriceController
from src.data.CoinData import CoinData
from src.data.DbData import DbWebsiteName
from src.db.DbPostgresql import DbPostgresql
from src.db.DbSqlite3 import DbSqlite3
from src.models.CoinPriceAlcor import CoinPriceAlcor
from src.models.CoinPriceCoingecko import CoinPriceCoingecko
from src.models.CoinPriceCryptowatch import CoinPriceCryptowatch
from src.views.CoinPriceViewCli import CoinPriceViewCli


def __main__():
    """Search assets and store in database"""
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "-d",
        "--date",
        type=str,
        help="Historical date to search, format: 2011-11-04T00:05:23+04:00",
        default="2022-05-01T23:00",
    )
    argparser.add_argument(
        "-w", "--website", type=str, help="Website / exchange to search on"
    )
    argparser.add_argument(
        "-c", "--coin", type=str, help="List of coins to search", required=False
    )
    argparser.add_argument(
        "-st",
        "--strictness",
        type=int,
        help="Cryptowatch: Strictness type for filtering currency in base",
        default=1,
    )
    argparser.add_argument(
        "-mp",
        "--max_markets_per_pair",
        type=int,
        help="Cryptowatch: Maximum markets per pair, 0 is no max",
        default=0,
    )
    argparser.add_argument(
        "-ch",
        "--chain",
        type=str,
        help="Alcor: Chain to search on Alcor, only in combination with coin",
    )

    args = argparser.parse_args()
    date = args.date
    coin_str = args.coin
    strictness = args.strictness
    max_markets_per_pair = args.max_markets_per_pair

    # init session
    search_website = str(args.website).lower()
    chain_str = ""
    if search_website == DbWebsiteName.ALCOR.name.lower():
        cp = CoinPriceAlcor()
        chain_str = args.chain if args.chain != None else "proton"
    elif search_website == DbWebsiteName.CRYPTOWATCH.name.lower():
        cp = CoinPriceCryptowatch(
            strictness=strictness, max_markets_per_pair=max_markets_per_pair
        )
    else:
        cp = CoinPriceCoingecko()

    # init session
    if config.DB_TYPE == "sqlite":
        db = DbSqlite3(config.DB_CONFIG)
    elif config.DB_TYPE == "postgresql":
        db = DbPostgresql(config.DB_CONFIG)
    else:
        raise RuntimeError("No database configuration")

    # check if database and table coins exists and has values
    db.check_db()
    view = CoinPriceViewCli()
    app = CoinPriceController(view, cp, db)

    # Determine which coins to retrieve prices for
    # From arguments, from database, or take default
    if coin_str != None:
        coins = re.split("[;,]", coin_str)
        coin_data = [CoinData(siteid=i, chain=chain_str, symbol=i) for i in coins]
    elif cp.website_id > 0:
        coins = DbHelper.get_coins(db, "", cp.website_id)
        coin_data = [
            CoinData(siteid=i[0], name=i[1], symbol=i[2], chain=i[3], base=i[4])
            for i in coins
        ]
    else:
        # providing default values for price retrieving
        if search_website == DbWebsiteName.ALCOR.name.lower():
            coins = [
                ["proton", "157"],
                ["wax", "158"],
                ["proton", "13"],
                ["wax", "67"],
                ["proton", "5"],
                ["eos", "2"],
                ["telos", "34"],
                ["proton", "96"],
            ]
            coin_data = [CoinData(siteid=i[1], chain=i[0]) for i in coins]
        elif search_website == DbWebsiteName.CRYPTOWATCH.name.lower():
            coins = ["btc", "ltc", "ada", "sol", "ardr", "xpr"]
            coin_data = [CoinData(siteid=i, symbol=i) for i in coins]
        else:
            coins = ["bitcoin", "litecoin", "cardano", "solana", "ardor", "proton"]
            coin_data = [CoinData(siteid=i) for i in coins]

    app.run(coin_data=coin_data, date=date)


if __name__ == "__main__":
    __main__()
