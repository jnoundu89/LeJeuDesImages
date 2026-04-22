"""Runtime registry of active datasets, resolved per-request via cookie."""
from typing import Optional

from flask import Request

from models.config import AppConfig, DatasetConfig
from models.dataset import Dataset

DATASET_COOKIE = 'dataset'


class DatasetRegistry:
    """Keeps one Dataset instance per id and picks the active one from the request.

    The active dataset for a request is determined by the `dataset` cookie,
    falling back to the registry's default id when the cookie is missing or
    points to an unknown dataset.
    """

    def __init__(self, default_id: str = ''):
        self._datasets: dict[str, Dataset] = {}
        self._default_id = default_id

    @classmethod
    def from_app_config(cls, app_config: AppConfig) -> 'DatasetRegistry':
        registry = cls(default_id=app_config.default_dataset_id)
        for ds_config in app_config.datasets.values():
            registry.add(ds_config)
        return registry

    def add(self, config: DatasetConfig) -> Dataset:
        dataset = Dataset(config)
        self._datasets[config.id] = dataset
        if not self._default_id:
            self._default_id = config.id
        return dataset

    def remove(self, dataset_id: str) -> None:
        self._datasets.pop(dataset_id, None)
        if self._default_id == dataset_id:
            self._default_id = next(iter(self._datasets), '')

    def get(self, dataset_id: str) -> Optional[Dataset]:
        return self._datasets.get(dataset_id)

    def ids(self) -> list[str]:
        return list(self._datasets.keys())

    def values(self) -> list[Dataset]:
        return list(self._datasets.values())

    def is_empty(self) -> bool:
        return not self._datasets

    @property
    def default_id(self) -> str:
        return self._default_id

    def set_default(self, dataset_id: str) -> None:
        if dataset_id not in self._datasets:
            raise KeyError(f'Unknown dataset id: {dataset_id}')
        self._default_id = dataset_id

    def current_id(self, request: Request) -> str:
        """Resolve the active dataset id for this request (cookie → default)."""
        cookie_id = request.cookies.get(DATASET_COOKIE)
        if cookie_id and cookie_id in self._datasets:
            return cookie_id
        return self._default_id

    def current(self, request: Request) -> Optional[Dataset]:
        return self.get(self.current_id(request))
