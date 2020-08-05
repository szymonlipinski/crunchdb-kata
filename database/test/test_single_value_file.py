import os
from random import randrange

from .common import temp_file
from ..file_format import SingleValueDataFile, SingleValue

# this is a workaround, so the automated tools won't remove the import as unused
temp_file


def test_non_existing_file():
    """For non existing file, we should get an empty list when reading the values."""
    data_file = SingleValueDataFile("akjdhakjdhas")
    a = list(data_file.read())
    assert a == []


def test_writing_one_value(temp_file):
    """We should be able to write and read one value, the file should have good size."""
    data_file = SingleValueDataFile(temp_file)
    value = SingleValue(pk=123, value=456)
    data_file.write(value)
    assert 6 == os.path.getsize(temp_file)
    assert [value] == list(data_file.read())


def test_writing_two_values(temp_file):
    """We should be able to write and read two values, the file should have good size."""
    data_file = SingleValueDataFile(temp_file)
    values = [SingleValue(pk=123, value=456), SingleValue(pk=44123, value=44456)]
    for value in values:
        data_file.write(value)
    assert 6 * len(values) == os.path.getsize(temp_file)
    assert values == list(data_file.read())


def test_writing_multiple_values(temp_file):
    """We should be able to write and read multiple values, the file should have good size."""
    data_file = SingleValueDataFile(temp_file)

    min = 0
    max = 1234
    max_length = randrange(2000, 3000)

    values = [SingleValue(randrange(min, max), randrange(min, max)) for _ in range(1, randrange(0, max_length))]

    for value in values:
        data_file.write(value)

    assert 6 * len(values) == os.path.getsize(temp_file)
    assert values == list(data_file.read())
