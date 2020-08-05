from ..db import Database, DatabaseConfigException
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
    ]
    for config_name, expected_message in params:
        try:
            tmpdir = mkdtemp(prefix="crunch_test_")

            if config_name:
                copy_config(config_name, tmpdir)

            Database(tmpdir)

        except DatabaseConfigException as e:
            assert expected_message.format(tmpdir=tmpdir) in str(e)

        finally:
            rmtree(tmpdir)
