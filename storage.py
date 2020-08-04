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
from database.db import Database

log = logging.getLogger(__name__)


@dataclass
class Config:
    """Class for storing command line arguments."""

    db_connection: str
    db_name: str
    db_collection: str
    storage_dir: str
    batch_size: int


@dataclass
class Session:
    """Class for storing global runtime variables."""

    config: Config
    collection: Collection
    storage: Database


def start_data_watcher(session: Session) -> None:
    """Runs the data watcher.

    Downloads the data in batches of exact {--batch-size} number of elements
    and stores it on disk.

    It sleeps for a couple of seconds between the checks unless there is lots of documents to fetch.
    Then it's fetching as fast as possible.

    """

    collection = session.collection
    documents_filter = {FETCHED_FIELD_NAME: False}
    sleep_time = 10

    while True:
        documents_count = collection.count_documents(documents_filter)
        log.info(f"found {documents_count} documents for fetching")

        if documents_count < session.config.batch_size:
            log.info(f"going to sleep for {sleep_time} seconds")
            sleep(sleep_time)
            continue

        for document in collection.find(documents_filter, limit=session.config.batch_size):
            log.info(f"Downloaded document: {document['_id']}")

            session.storage.store_answer(document)

            collection.update_one({"_id": document["_id"]}, {"$set": {FETCHED_FIELD_NAME: True}})
            log.info(f"Updated document: {document['_id']}")

        sleep(0.2)


@click.command()
@click.option(
    "--storage-dir",
    default=CONFIG_DEFAULT_STORAGE_DIR,
    show_default=True,
    help=f"Data directory with the storage files.",
)
@click.option(
    "--db-connection",
    default=CONFIG_DEFAULT_MONGODB_CONNECTION_STRING,
    show_default=True,
    help="Connection string for the MongoDB database.",
)
@click.option(
    "--db-name", default=CONFIG_DEFAULT_MONGODB_DB_NAME, show_default=True, help="Name of the MongoDB database.",
)
@click.option(
    "--db-collection",
    default=CONFIG_DEFAULT_MONGODB_COLLECTION_NAME,
    show_default=True,
    help="Name of the MongoDB collection.",
)
@click.option(
    "--batch-size",
    default=CONFIG_DEFAULT_STORAGE_BATCH_SIZE,
    show_default=True,
    help="Size of the batch to download from MongoDB.",
)
def run(storage_dir, db_collection, db_name, db_connection, batch_size):
    config = Config(
        storage_dir=storage_dir,
        db_collection=db_collection,
        db_connection=db_connection,
        db_name=db_name,
        batch_size=batch_size,
    )
    session = Session(
        config=config,
        collection=get_db_collection(
            connection_str=config.db_connection, db_name=config.db_name, collection_name=config.db_collection,
        ),
        storage=Database(config.storage_dir),
    )

    start_data_watcher(session)


if __name__ == "__main__":
    run()
