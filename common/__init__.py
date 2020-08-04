import logging

from bson import CodecOptions, SON
from pymongo import MongoClient
from pymongo.collection import Collection
from typing import Any
from dataclasses import dataclass

FETCHED_FIELD_NAME = "_fetched"

CONFIG_DEFAULT_DATA_DIR = "data"
CONFIG_DEFAULT_MONGODB_CONNECTION_STRING = (
    f"mongodb://{MongoClient.HOST}:{MongoClient.PORT}"
)
CONFIG_DEFAULT_MONGODB_DB_NAME = "crunchdb"
CONFIG_DEFAULT_MONGODB_COLLECTION_NAME = "preferences"
CONFIG_DEFAULT_STORAGE_DIR = "storage_dir"
CONFIG_DEFAULT_STORAGE_BATCH_SIZE = 50

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)



def get_db_collection(
    connection_str: str, db_name: str, collection_name: str
) -> Collection:
    """Creates a mongodb connection.

    :return: MongoDB Collection object
    """
    client = MongoClient(connection_str)
    db = client[db_name]
    opts = CodecOptions(document_class=SON)
    return db[collection_name].with_options(codec_options=opts)
