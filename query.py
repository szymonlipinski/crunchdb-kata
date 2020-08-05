"""
3. A python script (``query.py``) to read the data stored into the **system** and provide answers to one of the **questions**


We want to be able to answer these **questions**:

1. What's the most frequently owned car brand?
2. What's the favourite car brand?
3. What's the most listened to music artist?
4. What's the favourite music artist?

"""
"""
2. A python script (``storage.py``) to fetch the preferences from MongoDB and move them into the **system**

"""

import logging
from dataclasses import dataclass
from time import sleep

import click
from pymongo.collection import Collection

from common import (
    get_db_collection,
    CONFIG_DEFAULT_MONGODB_COLLECTION_NAME,
    CONFIG_DEFAULT_MONGODB_CONNECTION_STRING,
    CONFIG_DEFAULT_MONGODB_DB_NAME,
    CONFIG_DEFAULT_STORAGE_DIR,
    CONFIG_DEFAULT_STORAGE_BATCH_SIZE,
    FETCHED_FIELD_NAME,
)
from database.db import Database, Sorting

log = logging.getLogger(__name__)


@dataclass
class Question:

    question: str
    collection_name: str
    sorting: Sorting
    limit: 1


questions = [
    Question("What's the most frequently owned car brand?", "ever_owned_cars", Sorting.DESC, 1),
    Question("What's the favourite car brand?", "favourite_car_brand", Sorting.DESC, 1),
    Question("What's the most listened to music artist?", "listened_singers", Sorting.DESC, 1),
    Question("What's the favourite music artist?", "favourite_singer", Sorting.DESC, 1),
    Question("What are the three least known music artist?", "known_singers", Sorting.ASC, 3),
]


@dataclass
class Config:
    """Class for storing command line arguments."""

    storage_dir: str


@dataclass
class Session:
    """Class for storing global runtime variables."""

    config: Config
    storage: Database


@click.command()
@click.option(
    "--storage-dir",
    default=CONFIG_DEFAULT_STORAGE_DIR,
    show_default=True,
    help=f"Data directory with the storage files.",
)
def run(storage_dir):
    config = Config(storage_dir=storage_dir,)
    session = Session(config=config, storage=Database(config.storage_dir),)

    while True:
        for index, question in enumerate(questions):
            click.secho(f"  {index+1} - {question.question}", fg="green")

        value = click.prompt("Please choose the question number", type=int)
        if value < 1 or value > len(questions):
            click.secho("Bad number, choose again", fg="red")
            continue
        question = questions[value - 1]

        click.secho(f"\n The chosen question: {question.question}", fg="green")
        click.secho(f"Searching...", fg="green")

        search_result = session.storage.count(question.collection_name, limit=question.limit, sorting=question.sorting)

        click.secho(f"\nThe answer is:", fg="yellow")
        if len(search_result) == 1:
            click.secho(f"               {search_result[0].value}", fg="yellow")
        else:
            for index, result in enumerate(search_result):
                click.secho(f"               {index+1}. {result.value}", fg="yellow")

        click.secho("\nDo you want to search again?")


if __name__ == "__main__":
    run()
