import importlib
import pkgutil

import pytest

import models
from app import create_app
from models.config import CompanyConfig
from models.employee import EmployeeData
from models.game import GameManager
from models.game_mode import GameMode, GameModeFactory, NormalMode, ReverseMode
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


@pytest.fixture
def game_manager(test_employee_data, test_score_manager):
    return GameManager(test_employee_data, test_score_manager)


@pytest.fixture
def mode_factory(game_manager):
    factory = GameModeFactory(game_manager)
    # Auto-discover and register all modes (mirrors app.py logic)
    for _importer, modname, _ispkg in pkgutil.iter_modules(models.__path__):
        if modname.endswith('_mode') and modname != 'game_mode':
            module = importlib.import_module(f'models.{modname}')
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and issubclass(attr, GameMode)
                        and attr is not GameMode and attr not in (NormalMode, ReverseMode)):
                    instance = attr(game_manager)
                    factory.register_mode(instance)
    return factory


@pytest.fixture(scope='session')
def app():
    # Import the module-level app (already created with config.yaml or APP_CONFIG env)
    # Cannot call create_app() again because blueprints are singletons
    import os
    os.environ.setdefault('APP_CONFIG', 'tests/fixtures/test_config.yaml')
    from app import app as flask_app
    if flask_app is None:
        pytest.skip('Flask app could not be created (config.yaml missing?)')
    flask_app.config['TESTING'] = True
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()
