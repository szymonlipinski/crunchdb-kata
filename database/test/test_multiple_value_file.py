import os
from random import randrange

from .common import temp_file
from ..file_format import MultiValueDataFile, MultiValue
from typing import List

# this is a workaround, so the automated tools won't remove the import as unused
temp_file


def test_non_existing_file():
    """For non existing file, we should get an empty list when reading it."""
    data_file = MultiValueDataFile("akjdhakjdhas", 10)
    a = list(data_file.read())
    assert a == []


def test_writing_one_value(temp_file):
    """We should be able to write and read one value, the file should have good size."""
    data_file = MultiValueDataFile(temp_file, 10)
    value = MultiValue(pk=123, yes_choices=[0, 1, 2, 3], no_choices=[7, 8, 9])
    data_file.write(value)
    assert (4 + 2 + 2) == os.path.getsize(temp_file)
    assert [value] == list(data_file.read())


def test_writing_two_values(temp_file):
    """We should be able to write and read two value, the file should have good size."""
    data_file = MultiValueDataFile(temp_file, 36)
    values = [
        MultiValue(pk=123, yes_choices=[0, 1, 2, 3], no_choices=[7, 8, 9]),
        MultiValue(pk=990, yes_choices=[33], no_choices=[]),
    ]
    for value in values:
        data_file.write(value)

    # the expected size is:
    #   pk  [4B]
    #   yes [36b rounded to 40b = 5B]
    #   no  [36b rounded to 40b = 5B]
    assert (4 + 5 + 5) * len(values) == os.path.getsize(temp_file)
    assert values == list(data_file.read())


def make_unique_int_list(min: int, max: int, max_length: int) -> List[int]:
    return sorted(list(set([randrange(min, max) for _ in range(0, randrange(0, max_length))])))


def test_writing_multiple_values(temp_file):
    """We should be able to write and read one value, the file should have good size."""
    data_file = MultiValueDataFile(temp_file, 1998)

    min = 0
    max = 1234
    max_length = randrange(2000, 2200)

    values = [
        MultiValue(
            pk=randrange(min, max),
            yes_choices=make_unique_int_list(min, max, max_length),
            no_choices=make_unique_int_list(min, max, max_length),
        )
        for _ in range(1, randrange(0, max_length))
    ]

    for value in values:
        data_file.write(value)

    # the expected size is:
    #   pk  [4B]
    #   yes [1998b rounded to 2000b = 250B]
    #   no  [1998b rounded to 2000b = 250B]
    assert (4 + 250 + 250) * len(values) == os.path.getsize(temp_file)
    assert values == list(data_file.read())
