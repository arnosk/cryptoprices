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


class CoinInsertStatus(Enum):
    """Class for enumerating status
    """
    NO_DATABASE = auto()
    COIN_EXISTS = auto()
    INSERT_OK = auto()
    INSERT_ERROR = auto()
