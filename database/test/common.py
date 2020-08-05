import os
import shutil
from tempfile import mkdtemp, mkstemp
from shutil import copyfile
import pytest


@pytest.fixture
def temp_dir():
    """Pytest fixture which creates a temporary directory and removes it after the test."""
    tmpdir = mkdtemp(prefix="crunch_test_")
    yield tmpdir
    shutil.rmtree(tmpdir)


@pytest.fixture
def temp_file():
    """Pytest fixture which creates a temporary file and removes it after the test."""
    fd, path = mkstemp(prefix="crunch_test_")
    os.close(fd)
    yield path
    os.remove(path)


def copy_config(fname: str, to_dir: str) -> None:
    """Copies the file to the destination directory as the config file.

    Notes:
        * If the file doesn't end with ".json" the ".json" is added to it.
        * The file is copied from the test/sample_files directory.
        * The file is copied as to_dir/config.json

    Args:
        fname: Name of the file to copy.
        to_dir: Directory to copy the file to.
    """
    if not fname.endswith(".json"):
        fname += ".json"
    source_path = os.path.join(os.path.dirname(__file__), "sample_files", fname)
    destination_path = os.path.join(to_dir, "config.json")
    copyfile(source_path, destination_path)
