"""
@author: Arno
@created: 2022-12-26
@modified: 2023-05-20

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
