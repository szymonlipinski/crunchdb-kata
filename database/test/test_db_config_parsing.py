from ..db import Database, DatabaseConfigException
import pytest
from .common import temp_dir, copy_config
import os
from json.decoder import JSONDecodeError
from shutil import copyfile

# this is a workaround, so the automated tools won't remove the import as unused
temp_dir


def test_no_config_file():
    """Constructing the object should fail when the config file is not present."""
    with pytest.raises(DatabaseConfigException) as e:
        Database("aaa")
    assert "No such file or directory: 'aaa/config.json'" in str(e.value)


def test_bad_json(temp_dir):
    copy_config("bad_json", temp_dir)

    with pytest.raises(DatabaseConfigException) as e:
        Database(temp_dir)
    assert "Expecting value: line 1 column 1 (char 0)" in str(e.value)


def test_json_with_missing_choices(temp_dir):
    copy_config("missing_choices", temp_dir)

    with pytest.raises(DatabaseConfigException) as e:
        Database(temp_dir)

    assert "Missing 'choices' section of the config file." in str(e.value)


def test_json_with_bad_choices_format(temp_dir):
    copy_config("bad_choices_format", temp_dir)

    with pytest.raises(DatabaseConfigException) as e:
        Database(temp_dir)

    assert "The 'choices' section should be a dictionary." in str(e.value)


def test_json_with_missing_collections(temp_dir):
    copy_config("missing_collections", temp_dir)

    with pytest.raises(DatabaseConfigException) as e:
        Database(temp_dir)

    assert "Missing 'collections' section of the config file." in str(e.value)


def test_json_with_bad_collections_format(temp_dir):
    copy_config("bad_collections_format", temp_dir)

    with pytest.raises(DatabaseConfigException) as e:
        Database(temp_dir)

    assert "The 'collections' section should be a dictionary." in str(e.value)
