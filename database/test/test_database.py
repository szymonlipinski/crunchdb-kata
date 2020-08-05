import pytest

from .common import copy_config, temp_dir
from ..db import Database, AggregatedAnswer, Sorting, SearchAnswer

# this is a workaround, so the automated tools won't remove the import as unused
temp_dir

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


def assert_answer(expected_answer: SearchAnswer, current_answer: SearchAnswer):
    """Function asserts that both answers are the same for the fields: `results`, `data_size`.

    For the `time` field, we only check if `time > 0`.

    """
    assert expected_answer.results == current_answer.results
    assert expected_answer.data_size == current_answer.data_size
    assert current_answer.time >= 0.0


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

    expected = SearchAnswer(
        results=[AggregatedAnswer(value="brand_two", count=0), AggregatedAnswer(value="brand_one", count=0)],
        time=0.0,
        data_size=0,
    )
    assert_answer(expected, db.count("collection_two"))

    # check sorting

    expected = SearchAnswer(
        results=[AggregatedAnswer(value="brand_two", count=0), AggregatedAnswer(value="brand_one", count=0)],
        time=0.0,
        data_size=0,
    )
    assert_answer(expected, db.count("collection_two", sorting=Sorting.DESC))

    expected = SearchAnswer(
        results=[AggregatedAnswer(value="brand_one", count=0), AggregatedAnswer(value="brand_two", count=0)],
        time=0.0,
        data_size=0,
    )
    assert_answer(expected, db.count("collection_two", sorting=Sorting.ASC))

    # check limit and sorting
    expected = SearchAnswer(results=[AggregatedAnswer(value="brand_two", count=0)], time=0.0, data_size=0,)
    assert_answer(expected, db.count("collection_two", sorting=Sorting.DESC, limit=1))

    expected = SearchAnswer(results=[AggregatedAnswer(value="brand_one", count=0)], time=0.0, data_size=0,)
    assert_answer(expected, db.count("collection_two", sorting=Sorting.ASC, limit=1))


def test_count_for_empty_collection_for_multiple_choices(temp_dir):
    """For an empty collection with multiple choices we should get data with zeros only."""
    copy_config("good_sample_config", temp_dir)
    db = Database(temp_dir)

    expected = SearchAnswer(
        results=[
            AggregatedAnswer(value="singer_two", count=0),
            AggregatedAnswer(value="singer_three", count=0),
            AggregatedAnswer(value="singer_one", count=0),
        ],
        time=0.0,
        data_size=0,
    )
    assert_answer(expected, db.count("collection_one"))

    # check sorting
    expected = SearchAnswer(
        results=[
            AggregatedAnswer(value="singer_two", count=0),
            AggregatedAnswer(value="singer_three", count=0),
            AggregatedAnswer(value="singer_one", count=0),
        ],
        time=0.0,
        data_size=0,
    )
    assert_answer(expected, db.count("collection_one", sorting=Sorting.DESC))

    expected = SearchAnswer(
        results=[
            AggregatedAnswer(value="singer_one", count=0),
            AggregatedAnswer(value="singer_three", count=0),
            AggregatedAnswer(value="singer_two", count=0),
        ],
        time=0.0,
        data_size=0,
    )
    assert_answer(expected, db.count("collection_one", sorting=Sorting.ASC))

    # check limit and sorting
    expected = SearchAnswer(results=[AggregatedAnswer(value="singer_two", count=0)], time=0.0, data_size=0,)
    assert_answer(expected, db.count("collection_one", sorting=Sorting.DESC, limit=1))

    expected = SearchAnswer(
        results=[AggregatedAnswer(value="singer_one", count=0), AggregatedAnswer(value="singer_three", count=0)],
        time=0.0,
        data_size=0,
    )
    assert_answer(expected, db.count("collection_one", sorting=Sorting.ASC, limit=2))


def test_database_with_simple_data(temp_dir):
    """Check the values read from a good sample config.

    This is a very simple example, there is not too much data.
    However, it's great for debugging a simple happy path.

    """
    copy_config("good_sample_config", temp_dir)
    db = Database(temp_dir)

    answer = {
        "pk": "1",
        "collection_one.singer_one": "yes",
        "collection_one.singer_two": "no",
        "collection_one.singer_three": "not_answered",
        "collection_two": "brand_two",
    }

    db.store_answer(answer)

    expected = SearchAnswer(
        results=[
            AggregatedAnswer(value="singer_one", count=1),
            AggregatedAnswer(value="singer_two", count=0),
            AggregatedAnswer(value="singer_three", count=0),
        ],
        time=0.0,
        data_size=1,
    )
    assert_answer(expected, db.count("collection_one"))

    expected = SearchAnswer(
        results=[AggregatedAnswer(value="brand_two", count=1), AggregatedAnswer(value="brand_one", count=0)],
        time=0.0,
        data_size=1,
    )
    assert_answer(expected, db.count("collection_two"))


def test_database_with_complicated_data(temp_dir):
    """Check the values read from a good sample config.

    This is a a little bit more complicated case.
    """
    copy_config("good_sample_config", temp_dir)
    db = Database(temp_dir)

    """
    The below data is:

     Y => yes
     N => no
     - => not_answered

    collection_one:
    --------------------------------------
         :pk:     | 1 2 3 4 5 | total yes
    --------------------------------------
     singer_one   | Y Y N - - |     2
     singer_two   | N N Y - Y |     2
     singer_three | Y Y Y - Y |     4
    --------------------------------------

    collection_two:

      + => chosen
      - => not chosen

    --------------------------------------
         :pk:     | 1 2 3 4 5 | total yes
    --------------------------------------
      brand_one   | - - - + + |     2
      brand_two   | + + + - - |     3
    --------------------------------------

    """
    answers = [
        {
            "pk": "1",
            "collection_one.singer_one": "yes",
            "collection_one.singer_two": "no",
            "collection_one.singer_three": "yes",
            "collection_two": "brand_two",
        },
        {
            "pk": "2",
            "collection_one.singer_one": "yes",
            "collection_one.singer_two": "no",
            "collection_one.singer_three": "yes",
            "collection_two": "brand_two",
        },
        {
            "pk": "3",
            "collection_one.singer_one": "no",
            "collection_one.singer_two": "yes",
            "collection_one.singer_three": "yes",
            "collection_two": "brand_two",
        },
        {
            "pk": "4",
            "collection_one.singer_one": "not_answered",
            "collection_one.singer_two": "not_answered",
            "collection_one.singer_three": "not_answered",
            "collection_two": "brand_one",
        },
        {
            "pk": "5",
            "collection_one.singer_one": "not_answered",
            "collection_one.singer_two": "yes",
            "collection_one.singer_three": "yes",
            "collection_two": "brand_one",
        },
        # here the pk is repeating, so this should be not updated
        {
            "pk": "4",
            "collection_one.singer_one": "yes",
            "collection_one.singer_two": "yes",
            "collection_one.singer_three": "yes",
            "collection_two": "brand_two",
        },
        {
            "pk": "5",
            "collection_one.singer_one": "yes",
            "collection_one.singer_two": "yes",
            "collection_one.singer_three": "yes",
            "collection_two": "brand_one",
        },
    ]
    for answer in answers:
        db.store_answer(answer)

    expected = SearchAnswer(
        results=[
            AggregatedAnswer(value="singer_three", count=4),
            AggregatedAnswer(value="singer_two", count=2),
            AggregatedAnswer(value="singer_one", count=2),
        ],
        time=0.0,
        data_size=5,
    )
    assert_answer(expected, db.count("collection_one"))

    # check sorting
    expected = SearchAnswer(
        results=[
            AggregatedAnswer(value="singer_three", count=4),
            AggregatedAnswer(value="singer_two", count=2),
            AggregatedAnswer(value="singer_one", count=2),
        ],
        time=0.0,
        data_size=5,
    )
    assert_answer(expected, db.count("collection_one", sorting=Sorting.DESC))

    expected = SearchAnswer(
        results=[
            AggregatedAnswer(value="singer_one", count=2),
            AggregatedAnswer(value="singer_two", count=2),
            AggregatedAnswer(value="singer_three", count=4),
        ],
        time=0.0,
        data_size=5,
    )
    assert_answer(expected, db.count("collection_one", sorting=Sorting.ASC))

    # check limits

    expected = SearchAnswer(
        results=[AggregatedAnswer(value="singer_three", count=4), AggregatedAnswer(value="singer_two", count=2)],
        time=0.0,
        data_size=5,
    )
    assert_answer(expected, db.count("collection_one", sorting=Sorting.DESC, limit=2))

    expected = SearchAnswer(
        results=[AggregatedAnswer(value="singer_one", count=2), AggregatedAnswer(value="singer_two", count=2)],
        time=0.0,
        data_size=5,
    )
    assert_answer(expected, db.count("collection_one", sorting=Sorting.ASC, limit=2))

    # check collection_two
    expected = SearchAnswer(
        results=[AggregatedAnswer(value="brand_two", count=3), AggregatedAnswer(value="brand_one", count=2)],
        time=0.0,
        data_size=5,
    )
    assert_answer(expected, db.count("collection_two"))

    # check sorting
    expected = SearchAnswer(
        results=[AggregatedAnswer(value="brand_two", count=3), AggregatedAnswer(value="brand_one", count=2)],
        time=0.0,
        data_size=5,
    )
    assert_answer(expected, db.count("collection_two", sorting=Sorting.DESC))

    expected = SearchAnswer(
        results=[AggregatedAnswer(value="brand_one", count=2), AggregatedAnswer(value="brand_two", count=3)],
        time=0.0,
        data_size=5,
    )
    assert_answer(expected, db.count("collection_two", sorting=Sorting.ASC))

    # check limits
    expected = SearchAnswer(results=[AggregatedAnswer(value="brand_two", count=3)], time=0.0, data_size=5,)
    assert_answer(expected, db.count("collection_two", sorting=Sorting.DESC, limit=1))

    expected = SearchAnswer(results=[AggregatedAnswer(value="brand_one", count=2)], time=0.0, data_size=5,)
    assert_answer(expected, db.count("collection_two", sorting=Sorting.ASC, limit=1))
