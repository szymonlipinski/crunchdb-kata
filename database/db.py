"""
Database storage_dir.
"""

import json
import os.path
from dataclasses import dataclass
from enum import Enum
from typing import List


class Sorting(Enum):
    ASC = "asc"
    DESC = "desc"


@dataclass
class AggregatedAnswer:
    value: str
    count: int


@dataclass
class Collection:
    name: str
    multiple_answers: bool
    choices_name: str


class Database():
    """Main database API."""

    CONFIG_FILE_NAME = "config.json"

    def __init__(self, directory: str):
        self.directory = directory
        self.CONFIG_FILE_PATH = os.path.join(directory, self.CONFIG_FILE_NAME)
        self.choices = dict()
        self.collections = dict()

        self._read_config()

    def _read_config(self):
        """Reads the config file, makes basic validation."""
        with open(self.CONFIG_FILE_PATH) as f:
            config = json.loads(f)

        self.choices = config['choices']
        for collection in config['collections']:
            self._validate_collection(collection)
            self.collections[collection['name']] = Collection(**collection)

    def _validate_collection(self, collection: dict) -> None:
        """Validates if the collection has good data format."""
        pass

    def store_answer(self, collection: str, answer: dict) -> None:
        """Saves the answer to the collection."""
        pass

    def count(self, collection, first: int = 10, sorting: Sorting = Sorting.DESC) -> List[AggregatedAnswer]:
        """Counts the choices for the collection.

        returns:
            sorted in descending order list of all choices with the number of preferences
        """
        pass
