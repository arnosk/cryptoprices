"""
Created on May 5, 2023

@author: arno

Data enumerations for database 

"""
from dataclasses import dataclass
from enum import Enum, auto


class DbWebsiteName(Enum):
    """Class for enumerating website / exchange names
    """
    COINGECKO = auto()
    CRYPTOWATCH = auto()
    ALCOR = auto()

class DbTableName(Enum):
    """Class for enumerating table names
    """
    COIN = 'coin'
    WEBSITE = 'website'

class DbResultStatus(Enum):
    """Class for enumerating status
    """
    NO_DATABASE = auto()
    NO_TABLE = auto()
    COIN_EXISTS = auto()
    COIN_NOT_EXISTS = auto()
    INSERT_OK = auto()
    INSERT_ERROR = auto()
    DELETE_OK = auto()
    DELETE_ERROR = auto()

