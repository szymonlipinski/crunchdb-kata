from typing import Any

import logging
import json
import os.path
from dataclasses import dataclass
from enum import Enum
from typing import List
from bitarray import bitarray

log = logging.getLogger(__name__)


@dataclass
class OneValue:
    pk: int
    value: int


@dataclass
class MultiValue:
    pk: int
    yes_choices: List[int]
    no_choices: List[int]


class DataFile:
    BYTEORDER = "big"

    def __init__(self, file_path: str):
        self.file_path = file_path

    def write(self, value: Any):
        raise NotImplementedError

    def read(self) -> Any:
        raise NotImplementedError

    def _to_two_bytes(self, value):
        return value.to_bytes(2, byteorder=self.BYTEORDER)

    def _to_four_bytes(self, value):
        return value.to_bytes(4, byteorder=self.BYTEORDER)

    def _from_bytes(self, value):
        return int.from_bytes(value, byteorder=self.BYTEORDER)


class IdsDataFile(DataFile):
    def write(self, value: int):
        with open(self.file_path, "ab") as f:
            f.write(self._to_four_bytes(value))

    def read(self):
        if not os.path.exists(self.file_path):
            return

        with open(self.file_path, "rb") as f:
            while True:
                value = f.read(4)
                if value:
                    yield self._from_bytes(value)
                else:
                    break


class OneValueDataFile(DataFile):
    def write(self, value: OneValue):
        with open(self.file_path, "ab") as f:
            f.write(self._to_four_bytes(value.pk))
            f.write(self._to_two_bytes(value.value))

    def read(self):
        if not os.path.exists(self.file_path):
            return

        with open(self.file_path, "rb") as f:
            while True:
                pk = f.read(4)
                value = f.read(2)
                if pk and value:
                    yield OneValue(pk=self._from_bytes(pk), value=self._from_bytes(value))
                else:
                    break


class MultiValueDataFile(DataFile):
    def __init__(self, file_path: str, size: int):
        super().__init__(file_path)
        self.size = size

        self.size_in_bytes = size // 8
        if size % 8 != 0:
            self.size_in_bytes += 1

    def write(self, value: MultiValue):
        yes_bits = bitarray(self.size)
        no_bits = bitarray(self.size)
        yes_bits.setall(0)
        no_bits.setall(0)

        for position in value.yes_choices:
            yes_bits[position] = 1

        for position in value.no_choices:
            no_bits[position] = 1

        with open(self.file_path, "ab") as f:
            f.write(self._to_four_bytes(value.pk))
            f.write(yes_bits.tobytes())
            f.write(no_bits.tobytes())

    def read(self) -> MultiValue:
        if not os.path.exists(self.file_path):
            return

        with open(self.file_path, "rb") as f:
            while True:
                pk = f.read(4)
                yes_value = f.read(self.size_in_bytes)
                no_value = f.read(self.size_in_bytes)
                if pk and yes_value and no_value:
                    yield MultiValue(
                        pk=self._from_bytes(pk),
                        yes_choices=bitarray().frombytes(yes_value),
                        no_choices=bitarray().frombytes(no_value),
                    )
                else:
                    break
