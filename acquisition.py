"""
1. A python script (``acquisition.py``) to load the **preferences** as they come and queue them into a MongoDB database

This is a very simplified version:

- it loads all the existing *.jsonl files stored in the source directory
- it monitors the source directory for new and modified files and loads the new/modified ones
- only files with new pk are loaded to the database, so there is no update

"""
import glob
import logging
import os
import time
from dataclasses import dataclass
from json import loads

import bson
import click
from bson.raw_bson import RawBSONDocument

from watchdog.events import (
    FileSystemEventHandler,
    EVENT_TYPE_CREATED,
    EVENT_TYPE_MODIFIED,
)
from watchdog.observers import Observer

from common import (
    get_db_collection,
    FETCHED_FIELD_NAME,
    CONFIG_DEFAULT_DATA_DIR,
    CONFIG_DEFAULT_MONGODB_COLLECTION_NAME,
    CONFIG_DEFAULT_MONGODB_CONNECTION_STRING,
    CONFIG_DEFAULT_MONGODB_DB_NAME,
    Session,
)

log = logging.getLogger(__name__)

JSON_FILE_EXTENSION = ".jsonl"


@dataclass
class Config:
    """Class for storing command line arguments."""

    data_dir: str
    db_connection: str
    db_name: str
    db_collection: str


def load_file(file_path: str, session: Session) -> None:
    """Loads the file to the databases.

    If there already is a file with the same pk, then nothing is done.

    The json is converted into BSON and it's stored like this in the database,
    so 
    """
    # TODO: add error info about update-in-progress files
    # TODO: doc about _fetched
    try:
        with open(file_path) as f:
            log.info(f"Loading {file_path}")
            chunk = loads(f.read())

            doc_id = chunk["pk"]
            chunk["_id"] = doc_id
            chunk[FETCHED_FIELD_NAME] = False

            chunk = RawBSONDocument(bson.BSON.encode(chunk))

            if session.collection.count_documents({"_id": doc_id}) != 0:
                log.info(f"Skipping - there is already a document with id={doc_id}")
            else:
                session.collection.insert_one(chunk)
    except Exception as e:
        log.error(f"{e}")


def load_existing_files(session: Session) -> None:
    """Loads all *.jsonl files from the given path.

    """
    for file_path in glob.iglob(
        os.path.join(session.config.data_dir, f"*{JSON_FILE_EXTENSION}")
    ):
        load_file(file_path, session)


class FilesEventHandler(FileSystemEventHandler):
    """Handler for loading the new and modified files.
    """

    def __init__(self, session: Session):
        super().__init__()
        self._session = session

    def on_any_event(self, event):
        if event.event_type in [EVENT_TYPE_CREATED, EVENT_TYPE_MODIFIED]:
            if event.src_path.endswith(JSON_FILE_EXTENSION):
                load_file(event.src_path, self._session)


def start_files_watcher(session: Session) -> None:
    observer = Observer()
    observer.schedule(
        FilesEventHandler(session), session.config.data_dir, recursive=True
    )
    log.info("Starting the file watcher.")
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


@click.command()
@click.option(
    "--data-dir",
    default=CONFIG_DEFAULT_DATA_DIR,
    show_default=True,
    help=f"Data directory with *{JSON_FILE_EXTENSION} files.",
)
@click.option(
    "--db-connection",
    default=CONFIG_DEFAULT_MONGODB_CONNECTION_STRING,
    show_default=True,
    help="Connection string for the MongoDB database.",
)
@click.option(
    "--db-name",
    default=CONFIG_DEFAULT_MONGODB_DB_NAME,
    show_default=True,
    help="Name of the MongoDB database.",
)
@click.option(
    "--db-collection",
    default=CONFIG_DEFAULT_MONGODB_COLLECTION_NAME,
    show_default=True,
    help="Name of the MongoDB collection.",
)
def run(db_collection, db_name, db_connection, data_dir):
    config = Config(
        data_dir=data_dir,
        db_collection=db_collection,
        db_connection=db_connection,
        db_name=db_name,
    )
    session = Session(
        config=config,
        collection=get_db_collection(
            connection_str=config.db_connection,
            db_name=config.db_name,
            collection_name=config.db_collection,
        ),
    )

    load_existing_files(session)
    start_files_watcher(session)


if __name__ == "__main__":
    run()
