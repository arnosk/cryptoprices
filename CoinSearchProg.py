"""
Created on December 29, 2022

@author: arno

Controller part for searching crypto coins on website / exchanges

"""
import argparse
import re

import config
from src.controllers.CoinSearchController import CoinSearchController
from src.data.DbData import DbWebsiteName
from src.db.DbPostgresql import DbPostgresql
from src.db.DbSqlite3 import DbSqlite3
from src.models.CoinSearch import SearchMethod
from src.models.CoinSearchAlcor import CoinSearchAlcor
from src.models.CoinSearchCoingecko import CoinSearchCoingecko
from src.models.CoinSearchCryptowatch import CoinSearchCryptowatch
from src.views.CoinSearchViewCli import CoinSearchViewCli


def __main__():
    """Search assets and store in database"""
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "-w", "--website", type=str, help="Website / exchange to search on"
    )
    argparser.add_argument(
        "-ch", "--chain", type=str, help="Alcor: Chain name to search on Alcor"
    )
    argparser.add_argument(
        "-i",
        "--image",
        action="store_true",
        help="Coingecko: Save image file for all coins from coingecko in database",
    )
    argparser.add_argument(
        "-s",
        "--searchweb",
        action="store_true",
        help="Coingecko: Search directly from CoinGecko website instead or first retrieving list of all assets",
    )
    args = argparser.parse_args()
    download_all_images = args.image

    if args.searchweb:
        search_method = SearchMethod.WEB
    else:
        search_method = SearchMethod.ASSETS

    # Select chain from argument or take default all chains (only for Alcor)
    chain_str = args.chain
    if chain_str != None:
        chains = re.split("[;,]", chain_str)
    else:
        chains = config.ALCOR_CHAINS

    # init session
    search_website = str(args.website).lower()
    if search_website == DbWebsiteName.ALCOR.name.lower():
        cs = CoinSearchAlcor(chains=chains)
    elif search_website == DbWebsiteName.CRYPTOWATCH.name.lower():
        cs = CoinSearchCryptowatch()
    else:
        cs = CoinSearchCoingecko(search_method=search_method)

    if config.DB_TYPE == "sqlite":
        db = DbSqlite3(config.DB_CONFIG)
    elif config.DB_TYPE == "postgresql":
        db = DbPostgresql(config.DB_CONFIG)
    else:
        raise RuntimeError("No database configuration")

    db.check_db()

    if download_all_images:
        cs = CoinSearchCoingecko()
        cs.download_images(db)
        print("Done downloading images")
        exit()

    view = CoinSearchViewCli()
    app = CoinSearchController(view, cs, db)
    app.run()


if __name__ == "__main__":
    __main__()
