import logging
import os.path
from dataclasses import dataclass
from typing import Any
from typing import List
from typing import Generator
from bitarray import bitarray
from abc import ABC

log = logging.getLogger(__name__)


@dataclass
class SingleValue:
    """Structure of data stored in the SingleValueFile.

    Attributes:
        pk: Primary key for the value.
        value: Answer selected by the user.
    """

    pk: int
    value: int


@dataclass
class MultiValue:
    """Structure of data store in the MultiValueFile.

    Attributes:
        pk: Primary key for the value.
        yes_choices: List of answers a user answered "yes".
        no_choices: List of answers a user answered "no".
    """

    pk: int
    yes_choices: List[int]
    no_choices: List[int]


class DataFile(ABC):
    """Base class for data manipulation using different files formats.

    Args:
        BYTEORDER: Order of the bytes used in the data files.
        file_path: Path of the data file.

    Attributes:
        BYTEORDER: Order of the bytes used in the data files.
        file_path: Path of the data file.
    """

    BYTEORDER = "big"

    def __init__(self, file_path: str):
        self.file_path = file_path

    def write(self, value: Any) -> None:
        """Writes a value to the data file.

        Args:
            value: Value to store in the file.
        """
        raise NotImplementedError

    def read(self) -> Generator[Any, None, None]:
        """Yields a value from the data file.

        Yields:
            Value read from the file.
        """
        raise NotImplementedError

    def _to_two_bytes(self, value: int) -> bytes:
        """Converts the argument to two byte array representing the value.

        Args:
            value: value to convert

        Returns:
            Two byte array representing the value.
        """
        return value.to_bytes(2, byteorder=self.BYTEORDER)

    def _to_four_bytes(self, value: int) -> bytes:
        """Converts the argument to four byte array representing the value.

        Args:
            value: value to convert

        Returns:
            Four byte array representing the value.
        """
        return value.to_bytes(4, byteorder=self.BYTEORDER)

    def _from_bytes(self, value: bytes) -> int:
        """Converts the argument to an integer.

        Args:
            value: value to convert

        Returns:
            Integer represented by the value bytes.
        """
        return int.from_bytes(value, byteorder=self.BYTEORDER)


class IdsDataFile(DataFile):
    """Class for reading and writing 4 byte integers one by one.

    Args:
        BYTEORDER: Order of the bytes used in the data files.
        file_path: Path of the data file.

    Attributes:
        BYTEORDER: Order of the bytes used in the data files.
        file_path: Path of the data file.
    """

    def write(self, value: int) -> None:
        """Writes a value to the data file.

        Args:
            value: Value to store in the file.
        """
        with open(self.file_path, "ab") as f:
            f.write(self._to_four_bytes(value))

    def read(self) -> Generator[int, None, None]:
        """Yields a value from the data file.

        Yields:
            Value read from the file.
        """
        if not os.path.exists(self.file_path):
            return

        with open(self.file_path, "rb") as f:
            while True:
                value = f.read(4)
                if value:
                    yield self._from_bytes(value)
                else:
                    break


class SingleValueDataFile(DataFile):
    """Class for reading and writing SingleValue one by one.

    Args:
        BYTEORDER: Order of the bytes used in the data files.
        file_path: Path of the data file.

    Attributes:
        BYTEORDER: Order of the bytes used in the data files.
        file_path: Path of the data file.
    """

    def write(self, value: SingleValue) -> None:
        """Writes a value to the data file.

        Args:
            value: Value to store in the file.
        """
        with open(self.file_path, "ab") as f:
            f.write(self._to_four_bytes(value.pk))
            f.write(self._to_two_bytes(value.value))

    def read(self) -> Generator[SingleValue, None, None]:
        """Yields a value from the data file.

        Yields:
            Value read from the file.
        """
        if not os.path.exists(self.file_path):
            return

        with open(self.file_path, "rb") as f:
            while True:
                pk = f.read(4)
                value = f.read(2)
                if pk and value:
                    yield SingleValue(pk=self._from_bytes(pk), value=self._from_bytes(value))
                else:
                    break


class MultiValueDataFile(DataFile):
    """Class for reading and writing MultiValue one by one.

    Args:
        BYTEORDER: Order of the bytes used in the data files.
        file_path: Path of the data file.
        size: Size in bits of the `yes` and `no` fields.

    Attributes:
        BYTEORDER: Order of the bytes used in the data files.
        file_path: Path of the data file.
        size: Size in bits of the `yes` and `no` fields.
        size_in_bytes: Size in bytes of the `yes` and `no` fields.
    """

    def __init__(self, file_path: str, size: int):
        super().__init__(file_path)
        self.size = size

        self.size_in_bytes = size // 8
        if size % 8 != 0:
            self.size_in_bytes += 1

    def write(self, value: MultiValue):
        """Writes a value to the data file.

        Args:
            value: Value to store in the file.
        """
        yes_bits = bitarray(self.size, endian=self.BYTEORDER)
        no_bits = bitarray(self.size, endian=self.BYTEORDER)
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

    def _convert_bitarray_to_indices(self, value: bytes) -> List[int]:
        """Converts the argument to list of set bits.

        Args:
            value: Array of bytes.

        Returns:
            A sorted list of integers containing numbers of positions
            with set bits in the value.
        """
        res = []
        bits = bitarray(endian=self.BYTEORDER)
        bits.frombytes(value)

        for n in range(0, self.size):
            if bits[n]:
                res.append(n)

        return res

    def read(self) -> Generator[MultiValue, None, None]:
        """Yields a value from the data file.

        Yields:
            Value read from the file.
        """
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
                        yes_choices=self._convert_bitarray_to_indices(yes_value),
                        no_choices=self._convert_bitarray_to_indices(no_value),
                    )
                else:
                    break
