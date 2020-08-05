from ..db import Database, DatabaseConfigException, Choice, Collection
import pytest
from .common import temp_dir, copy_config
import os
from json.decoder import JSONDecodeError
from shutil import copyfile, rmtree
from tempfile import mkdtemp, mkstemp

# this is a workaround, so the automated tools won't remove the import as unused
temp_dir


def test_parsing_file():
    """This is a really, really ugly workaround.
    It's hard to use the temp_dir fixture and the parametrized tests at the same time.
    So, here I do it by hand.
    """

    params = [
        # config_file, expected exception message
        ("", "No such file or directory: '{tmpdir}/config.json'"),
        ("bad_json", "Expecting value: line 1 column 1 (char 0)"),
        ("missing_choices", "Missing 'choices' section of the config file."),
        ("bad_choices_format", "The 'choices' section should be a dictionary."),
        ("missing_collections", "Missing 'collections' section of the config file."),
        ("bad_collections_format", "The 'collections' section should be a dictionary."),
        ("choice_is_not_list", "Collection value should be a list."),
        ("collection_without_multiple_answers", "There should be the multiple_answers field for one."),
        ("collection_with_bad_multiple_answers", "Multiple_answers field should have values of true/false."),
        ("collection_without_choices", "There should be the choices field for one."),
        ("collection_with_bad_choice_value", "The choices field should have one of the choices as value."),
    ]
    for config_name, expected_message in params:

        try:
            tmpdir = mkdtemp(prefix="crunch_test_")

            if config_name:
                copy_config(config_name, tmpdir)

            Database(tmpdir)

        except DatabaseConfigException as e:
            assert expected_message.format(tmpdir=tmpdir) in str(e), f"... {config_name}"

        finally:
            rmtree(tmpdir)


def test_sample_good_config(temp_dir):
    """Check the values read from a good sample config."""
    copy_config("good_sample_config", temp_dir)
    db = Database(temp_dir)

    """ The sample config is:

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

    choices = db._choices
    assert ["carbrands", "singers"] == list(choices)
    assert choices["carbrands"] == Choice(
        name="carbrands", values=["brand_one", "brand_two"], dict_values={"brand_one": 0, "brand_two": 1}
    )
    assert choices["singers"] == Choice(
        name="singers",
        values=["singer_one", "singer_two", "singer_three"],
        dict_values={"singer_one": 0, "singer_two": 1, "singer_three": 2},
    )

    collections = db._collections
    assert ["collection_one", "collection_two"] == list(collections)
    assert collections["collection_one"] == Collection(
        name="collection_one", multiple_answers=True, choices_name="singers"
    )
    assert collections["collection_two"] == Collection(
        name="collection_two", multiple_answers=False, choices_name="carbrands"
    )


def test_good_production_config(temp_dir):
    """Good production config should be parsed without any problem."""
    copy_config("good_production_config", temp_dir)
    db = Database(temp_dir)
    choices = db._choices
    assert ["carbrands", "singers"] == list(choices)
    assert len(choices["carbrands"].values) == 271
    assert len(choices["singers"].values) == 556

    collections = db._collections
    assert [
        "disliked_singers",
        "ever_owned_cars",
        "favourite_car_brand",
        "favourite_singer",
        "known_singers",
        "liked_cars",
        "listened_singers",
        "owned_cars",
        "voted_candidate",
    ] == list(collections)
