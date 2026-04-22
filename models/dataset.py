"""Bundles all runtime state for a single dataset: data, scores, and game modes."""
import importlib
import pkgutil
from pathlib import Path

import models
from models.config import DatasetConfig
from models.employee import EmployeeData
from models.game import GameManager
from models.game_mode import GameMode, GameModeFactory, NormalMode, ReverseMode
from models.score import ScoreManager


class Dataset:
    """One dataset = its own CSV load, score DB, game manager, and mode factory.

    Auto-discovers GameMode subclasses from models/*_mode.py and registers them
    against the dataset's own GameManager so modes share no state across datasets.
    """

    def __init__(self, config: DatasetConfig):
        self.config = config
        self.employee_data = EmployeeData(config)
        Path(config.scores_db_path).parent.mkdir(parents=True, exist_ok=True)
        self.score_manager = ScoreManager(config.scores_db_path)
        self.game_manager = GameManager(self.employee_data, self.score_manager)
        self.mode_factory = GameModeFactory(self.game_manager)

        self._register_discovered_modes()

    def _register_discovered_modes(self) -> None:
        for _importer, modname, _ispkg in pkgutil.iter_modules(models.__path__):
            if not modname.endswith('_mode') or modname == 'game_mode':
                continue
            module = importlib.import_module(f'models.{modname}')
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if not (isinstance(attr, type) and issubclass(attr, GameMode)):
                    continue
                if attr in (GameMode, NormalMode, ReverseMode):
                    continue
                instance = attr(self.game_manager)
                self.mode_factory.register_mode(instance)

    @property
    def id(self) -> str:
        return self.config.id
