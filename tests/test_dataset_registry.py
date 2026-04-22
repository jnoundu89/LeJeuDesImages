from flask import Flask

from models.config import AppConfig, DatasetConfig
from models.dataset import Dataset
from models.dataset_registry import DATASET_COOKIE, DatasetRegistry


def _ds_config(ds_id: str, tmp_path, csv_content: str | None = None) -> DatasetConfig:
    """Build a DatasetConfig pointing at a tiny CSV written under tmp_path."""
    csv_path = tmp_path / f'{ds_id}.csv'
    csv_path.write_text(
        csv_content
        or 'firstName,lastName,photo_path,team,jobTitle,company,sex\n'
           'Alice,Dupont,alice.jpg,Eng,Dev,Acme,F\n'
           'Bob,Martin,bob.jpg,Sales,Rep,Acme,M\n'
    )
    return DatasetConfig(
        ds_id,
        {
            'company': {'name': f'Co {ds_id}'},
            'data': {
                'csv_path': str(csv_path),
                'images_dir': str(tmp_path / 'photos'),
                'scores_db_path': str(tmp_path / f'{ds_id}_scores.json'),
                'column_mapping': {
                    'first_name': 'firstName',
                    'last_name': 'lastName',
                    'photo': 'photo_path',
                    'team': 'team',
                    'job_title': 'jobTitle',
                    'company': 'company',
                    'sex': 'sex',
                },
            },
        },
    )


class TestDataset:
    def test_builds_full_runtime_stack(self, tmp_path):
        ds = Dataset(_ds_config('acme', tmp_path))

        assert ds.id == 'acme'
        assert ds.employee_data is not None
        assert ds.score_manager is not None
        assert ds.game_manager is not None
        assert ds.mode_factory is not None

    def test_auto_discovers_game_modes(self, tmp_path):
        ds = Dataset(_ds_config('acme', tmp_path))

        # Known modes exist; NormalMode + ReverseMode are registered by GameModeFactory
        mode_names = set(ds.mode_factory.modes.keys())
        assert 'pixelation' in mode_names
        assert 'normal' in mode_names
        assert 'reverse' in mode_names
        assert len(mode_names) > 10

    def test_card_game_mode_reference_set(self, tmp_path):
        ds = Dataset(_ds_config('acme', tmp_path))
        assert ds.card_game_mode is not None


class TestDatasetRegistry:
    def test_add_sets_default_when_first(self, tmp_path):
        registry = DatasetRegistry()
        registry.add(_ds_config('acme', tmp_path))
        assert registry.default_id == 'acme'

    def test_add_preserves_existing_default(self, tmp_path):
        registry = DatasetRegistry(default_id='acme')
        registry.add(_ds_config('acme', tmp_path))
        registry.add(_ds_config('client_x', tmp_path))
        assert registry.default_id == 'acme'

    def test_remove_updates_default(self, tmp_path):
        registry = DatasetRegistry()
        registry.add(_ds_config('acme', tmp_path))
        registry.add(_ds_config('client_x', tmp_path))
        registry.remove('acme')
        assert registry.default_id == 'client_x'
        assert registry.get('acme') is None

    def test_is_empty(self, tmp_path):
        registry = DatasetRegistry()
        assert registry.is_empty()
        registry.add(_ds_config('acme', tmp_path))
        assert not registry.is_empty()

    def test_ids_and_values(self, tmp_path):
        registry = DatasetRegistry()
        registry.add(_ds_config('acme', tmp_path))
        registry.add(_ds_config('client_x', tmp_path))
        assert set(registry.ids()) == {'acme', 'client_x'}
        assert len(registry.values()) == 2

    def test_current_id_from_cookie(self, tmp_path):
        registry = DatasetRegistry()
        registry.add(_ds_config('acme', tmp_path))
        registry.add(_ds_config('client_x', tmp_path))

        app = Flask(__name__)
        with app.test_request_context('/', headers={'Cookie': f'{DATASET_COOKIE}=client_x'}):
            from flask import request
            assert registry.current_id(request) == 'client_x'

    def test_current_id_fallback_to_default_when_cookie_missing(self, tmp_path):
        registry = DatasetRegistry()
        registry.add(_ds_config('acme', tmp_path))
        registry.add(_ds_config('client_x', tmp_path))

        app = Flask(__name__)
        with app.test_request_context('/'):
            from flask import request
            assert registry.current_id(request) == 'acme'

    def test_current_id_fallback_when_cookie_points_to_unknown(self, tmp_path):
        registry = DatasetRegistry()
        registry.add(_ds_config('acme', tmp_path))

        app = Flask(__name__)
        with app.test_request_context('/', headers={'Cookie': f'{DATASET_COOKIE}=ghost'}):
            from flask import request
            assert registry.current_id(request) == 'acme'

    def test_set_default_rejects_unknown(self, tmp_path):
        registry = DatasetRegistry()
        registry.add(_ds_config('acme', tmp_path))

        import pytest
        with pytest.raises(KeyError):
            registry.set_default('ghost')

    def test_from_app_config_builds_all_datasets(self, tmp_path):
        import yaml
        ds_a = _ds_config('acme', tmp_path)
        ds_b = _ds_config('client_x', tmp_path)
        config_path = tmp_path / 'app_config.yaml'
        config_path.write_text(yaml.dump({
            'app': {'contact_email': 'c@e.com', 'default_dataset': 'client_x'},
            'datasets': {
                'acme': ds_a.to_dict(),
                'client_x': ds_b.to_dict(),
            },
        }))
        app_config = AppConfig(str(config_path))
        registry = DatasetRegistry.from_app_config(app_config)

        assert set(registry.ids()) == {'acme', 'client_x'}
        assert registry.default_id == 'client_x'

    def test_per_dataset_score_isolation(self, tmp_path):
        registry = DatasetRegistry()
        registry.add(_ds_config('acme', tmp_path))
        registry.add(_ds_config('client_x', tmp_path))

        acme = registry.get('acme')
        client_x = registry.get('client_x')
        assert acme is not None and client_x is not None
        assert acme.score_manager is not client_x.score_manager

        acme.score_manager.update_score('user1', 5, stat_updates={'name': 1})
        assert acme.score_manager.get_user_score('user1')['score'] == 5
        # client_x's DB has nothing for user1 → auto-initialized to 0
        assert client_x.score_manager.get_user_score('user1')['score'] == 0
