import pytest

from models.config import CompanyConfig
from models.employee import EmployeeData
from models.score import ScoreManager


@pytest.fixture
def test_config():
    return CompanyConfig('tests/fixtures/test_config.yaml')


@pytest.fixture
def test_employee_data(test_config):
    return EmployeeData(test_config)


@pytest.fixture
def test_score_manager(tmp_path):
    db_path = str(tmp_path / 'test_scores.json')
    return ScoreManager(db_path)


@pytest.fixture(scope='session')
def app():
    from app import app as flask_app
    return flask_app
