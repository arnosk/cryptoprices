"""
Created on Nov 3, 2022

@author: arno

Database Helper function to create tables

"""
from enum import Enum, auto

from src.data.CoinData import CoinData
from src.db.Db import Db


class DbTableName(Enum):
    """Class for enumerating table names
    """
    COIN = 'coin'
    WEBSITE = 'website'


class DbWebsiteName(Enum):
    """Class for enumerating website / exchange names
    """
    COINGECKO = auto()
    CRYPTOWATCH = auto()
    ALCOR = auto()


def create_coin_table(db: Db):
    """Create a coin and a website table

    """
    primary_key = db.get_create_primary_key_str()
    query = f'''CREATE TABLE {DbTableName.WEBSITE.value} (
                id {primary_key},
                name VARCHAR(80) NOT NULL,
                url VARCHAR(80) NOT NULL,
                api VARCHAR(80)
                )
            '''
    db.execute(query)
    query = f'''CREATE TABLE {DbTableName.COIN.value} (
                id {primary_key},
                website_id INTEGER NOT NULL,
                chain VARCHAR(80),
                siteid VARCHAR(80) NOT NULL,
                name VARCHAR(80) NOT NULL,
                symbol VARCHAR(40) NOT NULL,
                base VARCHAR(80),
                CONSTRAINT FK_Website FOREIGN KEY (website_id) REFERENCES {DbTableName.WEBSITE.value}(id)
                )
            '''
    db.execute(query)


def insert_website(db: Db, website: str) -> int:
    """Insert definition of the website or exchange
    """
    query = f'INSERT INTO {DbTableName.WEBSITE.value} (name, url) VALUES(?,?)'
    args = (website, 'https://')
    res = db.execute(query, args)
    db.commit()
    return res


def get_website_id(db: Db, website: str) -> int:
    """Retrieves the website id 
    """
    query = f'SELECT id FROM {DbTableName.WEBSITE.value} WHERE name = ?'
    args = (website,)
    res = db.query(query, args)
    if len(res) > 0:
        return res[0][0]
    else:
        return 0


def insert_coin(db: Db, coin: CoinData, website_id: int) -> int:
    """Insert a new coin to the coins table

    return value = rowcount or total changes 
    """
    query = f'INSERT INTO {DbTableName.COIN.value} (website_id, siteid, name, symbol, chain, base) VALUES(?,?,?,?,?,?)'
    args = (website_id,
            coin.siteid,
            coin.name,  # also quote
            coin.symbol,  # also quote symbol
            coin.chain,
            coin.base)
    res = db.execute(query, args)
    db.commit()
    return res


def delete_coin(db: Db, siteid: str, website_id: int) -> int:
    """Delete an existing coin 

    return value = rowcount or total changes 
    """
    query = f'DELETE FROM {DbTableName.COIN.value} WHERE siteid=? AND website_id=?'
    args = (siteid, website_id)
    res = db.execute(query, args)
    db.commit()
    return res


def get_coin(db: Db, siteid: str, website_id: int) -> list:
    """Retrieves the coin from id 
    """
    query = f'SELECT * FROM {DbTableName.COIN.value} WHERE siteid=? AND website_id=?'
    args = (siteid, website_id)
    res = db.query(query, args)
    return res


def get_coins(db: Db, search: str, website_id: int) -> list:
    """Retrieves coins from search string
    """
    query = f'''SELECT siteid, name, symbol, chain, base FROM {DbTableName.COIN.value} WHERE
                website_id = {website_id} AND
                (siteid like ? or
                name like ? or
                symbol like ? or
                base like ?
                )
            '''
    n = query.count('?')
    args = (f'%{search}%',)*n
    res = db.query(query, args)
    return res


def check_coin_table(db: Db) -> bool:
    """Check existance of coin table
    """
    return db.check_table(DbTableName.COIN.value)
