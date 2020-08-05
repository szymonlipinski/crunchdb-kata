import os
import shutil
from tempfile import mkdtemp, mkstemp

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
