from ..file_format import IdsDataFile
from .common import temp_file

from tempfile import mkdtemp, mkstemp
import pytest
import shutil
import os
from random import randrange

# this is a workaround, so the automated tools won't remove the import as unused
temp_file


def test_non_existing_file():
    """For non existing file, we should get an empty list when reading it."""
    data_file = IdsDataFile("akjdhakjdhas")
    a = list(data_file.read())
    assert a == []


def test_writing_one_value(temp_file):
    """We should be able to write and read one value, the file should have good size."""
    data_file = IdsDataFile(temp_file)
    value = 123
    data_file.write(value)
    assert 4 == os.path.getsize(temp_file)
    assert [123] == list(data_file.read())


def test_writing_two_values(temp_file):
    """We should be able to write and read one value, the file should have good size."""
    data_file = IdsDataFile(temp_file)
    values = [123, 456]
    for value in values:
        data_file.write(value)
    assert 4 * len(values) == os.path.getsize(temp_file)
    assert values == list(data_file.read())


def test_writing_multiple_values(temp_file):
    """We should be able to write and read one value, the file should have good size."""
    data_file = IdsDataFile(temp_file)

    MIN = 0
    MAX = 1234
    MAX_LENGTH = randrange(200, 400)

    values = [randrange(MIN, MAX) for _ in range(1, randrange(0, MAX_LENGTH))]

    for value in values:
        data_file.write(value)

    assert 4 * len(values) == os.path.getsize(temp_file)
    assert values == list(data_file.read())
