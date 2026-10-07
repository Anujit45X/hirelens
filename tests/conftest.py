import pytest

from hirelens.database import write_database
from hirelens.generate import generate_data


@pytest.fixture(scope="session")
def data():
    return generate_data()


@pytest.fixture
def database(tmp_path, data):
    path = tmp_path / "test.db"
    write_database(data, path)
    return path
