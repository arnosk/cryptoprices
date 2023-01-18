"""
Created on December 26, 2022

@author: arno

Data enumerations for search view

"""
from enum import Enum, auto


class CoinInsertStatus(Enum):
    """Class for enumerating status
    """
    NO_DATABASE = auto()
    COIN_EXISTS = auto()
    INSERT_OK = auto()
    INSERT_ERROR = auto()
