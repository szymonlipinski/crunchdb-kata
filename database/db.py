import json
import logging
import os.path
from dataclasses import dataclass
from enum import Enum
from typing import List

from .file_format import IdsDataFile, MultiValueDataFile, SingleValue, SingleValueDataFile, MultiValue

log = logging.getLogger(__name__)


class Sorting(Enum):
    ASC = "asc"
    DESC = "desc"


class FileType(Enum):
    """Type of the data file.
    """

    SINGLE_VALUE = "single.data"
    MULTI_VALUE = "multi.data"
    IDS = "ids"


@dataclass
class AggregatedAnswer:
    """Class for storing the aggregated answer like counting number of occurrences."""

    value: str
    count: int


@dataclass
class Collection:
    """Data structure for information about a Collection."""

    name: str
    multiple_answers: bool
    choices_name: str


@dataclass
class Choice:
    """Data structure for information about a Choice."""

    name: str
    values: list
    dict_values: dict


class DatabaseConfigException(Exception):
    """Exception used by the Database class"""

    pass


class Database:
    """Main database API.

    Args:
        directory: data storage directory

    Attributes:
        CONFIG_FILE_NAME: name of the configuration file
        _CONFIG_FILE_PATH: path of the configuration file
        _ids: dictionary [collection_name->List[ids]]
        _choices: dictionary [choice_name->List[Choice]]
        _collections: dictionary [collection_name->List[Collection]]
    """

    CONFIG_FILE_NAME = "config.json"

    def __init__(self, directory: str):
        self._directory = directory
        self._CONFIG_FILE_PATH = os.path.join(directory, self.CONFIG_FILE_NAME)

        self._ids = dict()
        self._choices = dict()
        self._collections = dict()

        self._read_config()
        self._read_ids_files(self._collections.values())

    def _get_file_name(self, collection: Collection, file_type: FileType) -> str:
        """Creates a file name base one the collection and the file type.

        Examples:
            For a Collection with name `XXX` and file type `FileType.MULTI_VALUE`
            it will return: `XXX.multi.data`

        Args:
            collection: Collection to create the file name for.
            file_type: Type of the file to create the name for.

        Returns:
            New file name for the collection and type.
        """
        return os.path.join(self._directory, f"{collection.name}.{file_type.value}")

    def _read_ids_files(self, collections: List[Collection]) -> None:
        """Reads the ids files for the collections and stores them in self._ids.

        Args:
            collections: List of collections to read the ids files for.
        """
        for collection in collections:
            self._ids[collection.name] = []
            file_path = self._get_file_name(collection, FileType.IDS)
            self._ids[collection.name] = list(IdsDataFile(file_path).read())

    def _read_config(self) -> None:
        """Reads the config file, makes config file validation.
        """
        try:
            with open(self._CONFIG_FILE_PATH) as f:
                config = json.load(f)
        except Exception as e:
            raise DatabaseConfigException(f"{e}")

        self._validate_config(config)

        for name, values in config["choices"].items():
            # as we will be looking for the index of the value, we also need to have a dictionary with indices:
            self._choices[name] = Choice(name=name, values=values, dict_values={v: i for i, v in enumerate(values)},)

        for name, value in config["collections"].items():
            self._collections[name] = Collection(
                name=name, multiple_answers=value["multiple_answers"], choices_name=value["choices"],
            )

    def _validate_config(self, config: dict) -> None:
        """Validates if the config has good data format.

        The format is:

        {
            "choices" {
                "choice_one": [],
                "choice_two": [],
            }
            "collections": {
                "collection_one": {
                  "multiple_answers": true,
                  "choices": "choice_one"
                },
            }
        }

        Raises:
            AssertionError: in case of bad config file format

        Args:
            config: dictionary with parsed config.json file.
        """
        choices = config.get("choices")
        if choices is None:
            raise DatabaseConfigException("Missing 'choices' section of the config file.")

        if not isinstance(choices, dict):
            raise DatabaseConfigException("The 'choices' section should be a dictionary.")

        collections = config.get("collections")
        if collections is None:
            raise DatabaseConfigException("Missing 'collections' section of the config file.")

        if not isinstance(collections, dict):
            raise DatabaseConfigException("The 'collections' section should be a dictionary.")

        choice_names = list(choices)
        for _, value in choices.items():
            if not isinstance(value, list):
                raise DatabaseConfigException("Collection value should be a list.")

        for name, value in collections.items():
            ma = value.get("multiple_answers")
            if ma is None:
                raise DatabaseConfigException(f"There should be the multiple_answers field for {name}.")
            if ma not in [True, False]:
                raise DatabaseConfigException("Multiple_answers field should have values of true/false.")

            ch = value.get("choices")
            if ch is None:
                raise DatabaseConfigException(f"There should be the choices field for {name}.")
            if ch not in choice_names:
                raise DatabaseConfigException("The choices field should have one of the choices as value.")

    def store_answer(self, answer: dict) -> None:
        """Saves the answer to the collection.

        We don't support updates now, so if the answer is already stored, nothing will be written to any file.

        Args:
            answer: Answer to store as dictionary from parsed json.
        """
        pk = int(answer["pk"])
        for name, collection in self._collections.items():

            if pk in self._ids[collection.name]:
                log.info(f"There already is data for {collection} for pk={pk}, skipping it.")
                continue

            if collection.multiple_answers is False:
                value = answer[name]
                log.debug(f"one item, {name} -> {value}")
                self.write_to_one_answer_file(collection, pk, value)

            else:
                yes_choices = []
                no_choices = []
                for answer_key, answer_value in answer.items():
                    key_parts = answer_key.split(".")
                    if key_parts[0] != name:
                        continue
                    choice_name = ".".join(key_parts[1:])
                    print(choice_name)
                    if answer_value == "no":
                        no_choices.append(choice_name)
                    elif answer_value == "yes":
                        yes_choices.append(choice_name)
                    print(yes_choices)
                self.write_to_multi_answer_file(collection, pk, yes_choices, no_choices)

    def write_to_multi_answer_file(
        self, collection: Collection, pk: int, yes_choices: List[str], no_choices: List[str]
    ) -> None:
        """Writes answers to a multi value data file.

        Args:
            collection: Collection to write the value to.
            pk: Primary key of the answer.
            yes_choices: List of user selected choices where user answered "yes".
            no_choices:  List of user selected choices where user answered "no".

        """

        log.debug(f"Writing to {collection.name}: {pk}")

        print(self._choices[collection.choices_name].dict_values)

        int_yes_values = [self._choices[collection.choices_name].dict_values[value] for value in yes_choices]
        int_no_values = [self._choices[collection.choices_name].dict_values[value] for value in no_choices]

        print(f"int_yes_values {int_yes_values}")
        print(f"int_no_values {int_no_values}")

        self._ids[collection.name].append(pk)
        IdsDataFile(self._get_file_name(collection, FileType.IDS)).write(pk)

        data_file = MultiValueDataFile(
            self._get_file_name(collection, FileType.MULTI_VALUE), len(self._get_choices(collection))
        )
        value = MultiValue(pk=pk, yes_choices=int_yes_values, no_choices=int_no_values)
        data_file.write(value)

    def write_to_one_answer_file(self, collection: Collection, pk: int, value: str) -> None:
        """Writes answer to the SingleValue file.

        Args:
            collection: Collection to write the value to.
            pk: Primary key of the answer.
            value: Value to write to, in this case it's just the one chosen position.

        """
        int_value = self._choices[collection.choices_name].dict_values[value]
        log.debug(f"Writing to {collection.name}: {pk} -> {value}[{int_value}]")

        self._ids[collection.name].append(pk)
        IdsDataFile(self._get_file_name(collection, FileType.IDS)).write(pk)

        SingleValueDataFile(self._get_file_name(collection, FileType.SINGLE_VALUE)).write(
            SingleValue(pk=pk, value=int_value)
        )

    def _get_choices(self, collection):
        """Returns list of choices for the collection.

        Args:
            collection: Collection to find the choices for.

        Returns:
            List of choices for the collection.
        """
        return self._choices[collection.choices_name].values

    # TODO FIX DOC

    def count(self, collection_name: str, limit: int = 10, sorting: Sorting = Sorting.DESC) -> List[AggregatedAnswer]:
        """Counts the choices for the collection.

        In case of a multi choice collection, we count the answers where user chose "yes".

        All results are sorted by the count number (depending on the `sorting` argument).
        The results then are limited to the number of the `limit` argument.

        Args:
            collection_name: Name of the collection to count the data for.
            limit: Number of values to return.
            sorting: Sorting direction of the results.

        Returns:
            List of values with the count number.
        """
        collection = self._collections.get(collection_name)
        if collection is None:
            raise ValueError("Bad collection name.")

        choices = self._get_choices(collection)

        result = {n: 0 for n in range(0, len(choices))}

        if collection.multiple_answers:
            df = MultiValueDataFile(self._get_file_name(collection, FileType.MULTI_VALUE), len(choices))
            for answer in df.read():
                for yes in answer.yes_choices:
                    result[yes] += 1
        else:
            df = SingleValueDataFile(self._get_file_name(collection, FileType.SINGLE_VALUE))
            for answer in df.read():
                result[answer.value] += 1

        # we need to translate the indices into the values:
        result = {choices[index]: item for index, item in result.items()}

        return [
            AggregatedAnswer(name, value)
            for name, value in sorted(result.items(), key=lambda x: (x[1], x[0]), reverse=sorting == Sorting.DESC)[
                :limit
            ]
        ]
