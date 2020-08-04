import os
from random import randrange

from .common import temp_file
from ..file_format import IdsDataFile

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

    min = 0
    max = 1234
    max_length = randrange(2000, 3000)

    values = [randrange(min, max) for _ in range(1, randrange(0, max_length))]

    for value in values:
        data_file.write(value)

    assert 4 * len(values) == os.path.getsize(temp_file)
    assert values == list(data_file.read())
