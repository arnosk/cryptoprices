"""
Created on December 26, 2022

@author: arno

Data enumerations for view

"""
from dataclasses import dataclass
from enum import Enum, auto


@dataclass
class Command:
    """Class that represents a command for CLI view"""

    command: str
    arguments: list[str]

    def __post_init__(self):
        self.command = self.command.lower()
        self.arguments = [x.lower() for x in self.arguments]


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


class OutputFileType(Enum):
    """Class for output file types
    """
    XLSX = auto()
    CSV = auto()


class PriceFunction(Enum):
    """Class for naming method for the retrieving price functions
    """
    CURRENT = 'Current'
    HISTORICAL_SIMPLE = 'HistSimple'
    HISTORICAL_MARKETCHART = 'HistMarketchart'


class SearchFunction(Enum):
    """Class for naming search type function
    """
    INSERT = 'Insert'
    DELETE = 'Delete'
    NONE = ''
