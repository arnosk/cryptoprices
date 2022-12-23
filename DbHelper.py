"""
Created on Nov 3, 2022

@author: arno

Database Helper function to create tables

"""
from enum import Enum, auto

from Db import Db


class DbTableName(Enum):
    """Class for enumerating table names
    """
    coin = auto()
    website = auto()


class DbWebsiteName(Enum):
    """Class for enumerating website / exchange names
    """
    coingecko = auto()
    cryptowatch = auto()
    alcor = auto()


def create_coin_table(db: Db):
    """Create a coin and a website table

    """
    primary_key = db.get_create_primary_key_str()
    query = f'''CREATE TABLE {DbTableName.website.name} (
                id {primary_key},
                name VARCHAR(80) NOT NULL,
                url VARCHAR(80) NOT NULL,
                api VARCHAR(80)
                )
            '''
    db.execute(query)
    query = f'''CREATE TABLE {DbTableName.coin.name} (
                id {primary_key},
                website_id INTEGER NOT NULL,
                chain VARCHAR(80),
                siteid VARCHAR(80) NOT NULL,
                name VARCHAR(80) NOT NULL,
                symbol VARCHAR(40) NOT NULL,
                base VARCHAR(80),
                CONSTRAINT FK_Website FOREIGN KEY (website_id) REFERENCES {DbTableName.website.name}(id)
                )
            '''
    db.execute(query)


def insert_website(db: Db, website: str) -> int:
    """Insert definition of the website or exchange
    """
    query = f'INSERT INTO {DbTableName.website.name} (name, url) VALUES(?,?)'
    args = (website, 'https://')
    res = db.execute(query, args)
    db.commit()
    return res


def get_website_id(db: Db, website: str) -> int:
    """Retrieves the website id 
    """
    query = f'SELECT id FROM {DbTableName.website.name} WHERE name = ?'
    args = (website,)
    res = db.query(query, args)
    if len(res) > 0:
        return res[0][0]
    else:
        return 0
