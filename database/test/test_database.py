from ..db import Database, DatabaseConfigException, Choice, Collection, AggregatedAnswer, Sorting
import pytest
from .common import temp_dir, copy_config
import os
from json.decoder import JSONDecodeError
from shutil import copyfile, rmtree
from tempfile import mkdtemp, mkstemp

"""

The sample config file is:

 {
   "choices": {
     "carbrands": ["brand_one", "brand_two"],
     "singers": ["singer_one", "singer_two", "singer_three"]
   },
   "collections": {
     "collection_one": {
       "multiple_answers": true,
       "choices": "singers"
     },
     "collection_two": {
       "multiple_answers": false,
       "choices": "carbrands"
     }
   }
 }
"""


def test_database_count_for_missing_collection(temp_dir):
    """There should be an exception when asking for a missing collection name."""
    copy_config("good_sample_config", temp_dir)
    db = Database(temp_dir)
    with pytest.raises(ValueError) as e:
        db.count("BAD_COLLECTION")

    assert "Bad collection name" in str(e)


def test_count_for_empty_collection_for_single_choice(temp_dir):
    """For an empty collection with single choice we should get data with zeros only."""
    copy_config("good_sample_config", temp_dir)
    db = Database(temp_dir)

    expected = [
        AggregatedAnswer(value="brand_two", count=0),
        AggregatedAnswer(value="brand_one", count=0),
    ]
    assert expected == db.count("collection_two")

    # check sorting

    expected = [
        AggregatedAnswer(value="brand_two", count=0),
        AggregatedAnswer(value="brand_one", count=0),
    ]
    assert expected == db.count("collection_two", sorting=Sorting.DESC)

    expected = [
        AggregatedAnswer(value="brand_one", count=0),
        AggregatedAnswer(value="brand_two", count=0),
    ]
    assert expected == db.count("collection_two", sorting=Sorting.ASC)

    # check limit and sorting
    expected = [
        AggregatedAnswer(value="brand_two", count=0),
    ]
    assert expected == db.count("collection_two", sorting=Sorting.DESC, limit=1)

    expected = [
        AggregatedAnswer(value="brand_one", count=0),
    ]
    assert expected == db.count("collection_two", sorting=Sorting.ASC, limit=1)


def test_count_for_empty_collection_for_multiple_choices(temp_dir):
    """For an empty collection with multiple choices we should get data with zeros only."""
    copy_config("good_sample_config", temp_dir)
    db = Database(temp_dir)

    expected = [
        AggregatedAnswer(value="singer_two", count=0),
        AggregatedAnswer(value="singer_three", count=0),
        AggregatedAnswer(value="singer_one", count=0),
    ]
    assert expected == db.count("collection_one")

    # check sorting
    expected = [
        AggregatedAnswer(value="singer_two", count=0),
        AggregatedAnswer(value="singer_three", count=0),
        AggregatedAnswer(value="singer_one", count=0),
    ]
    assert expected == db.count("collection_one", sorting=Sorting.DESC)

    expected = [
        AggregatedAnswer(value="singer_one", count=0),
        AggregatedAnswer(value="singer_three", count=0),
        AggregatedAnswer(value="singer_two", count=0),
    ]
    assert expected == db.count("collection_one", sorting=Sorting.ASC)

    # check limit and sorting
    expected = [
        AggregatedAnswer(value="singer_two", count=0),
    ]
    assert expected == db.count("collection_one", sorting=Sorting.DESC, limit=1)

    expected = [
        AggregatedAnswer(value="singer_one", count=0),
        AggregatedAnswer(value="singer_three", count=0),
    ]
    assert expected == db.count("collection_one", sorting=Sorting.ASC, limit=2)


def test_database(temp_dir):
    """Check the values read from a good sample config.

    This is a very simple example, there is not too much data.
    However, it's great for debugging a simple happy path.

    """
    copy_config("good_sample_config", temp_dir)
    db = Database(temp_dir)

    response_1 = {
        "pk": "1",
        "collection_one.singer_one": "yes",
        "collection_one.singer_two": "no",
        "collection_one.singer_three": "not_answered",
        "collection_two": "brand_two",
    }

    db.store_answer(response_1)

    expected = [
        AggregatedAnswer(value="singer_one", count=1),
        AggregatedAnswer(value="singer_two", count=0),
        AggregatedAnswer(value="singer_three", count=0),
    ]

    assert expected == db.count("collection_one")

    expected = [
        AggregatedAnswer(value="brand_two", count=1),
        AggregatedAnswer(value="brand_one", count=0),
    ]
    assert expected == db.count("collection_two")
