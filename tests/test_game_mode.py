from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest

from models.game_mode import GameMode


# Concrete subclass for testing abstract GameMode
class _StubMode(GameMode):
    @property
    def name(self) -> str:
        return 'stub'

    @property
    def description(self) -> str:
        return 'A stub game mode for testing'

    @property
    def template(self) -> str:
        return 'stub.html'

    def get_question_data(self, data_id: int, used_indices: List[int],
                          current_question: int) -> Dict[str, Any]:
        return {}

    def update_score(self, user_id: int, **kwargs) -> None:
        pass


@pytest.fixture
def mock_game_manager(test_employee_data, test_score_manager):
    gm = MagicMock()
    gm.employee_data = test_employee_data
    gm.score_manager = test_score_manager
    return gm


@pytest.fixture
def stub_mode(mock_game_manager):
    return _StubMode(mock_game_manager)


class TestMakeFullName:
    def test_basic(self):
        emp = {'first_name': 'Alice', 'last_name': 'DUPONT'}
        assert GameMode._make_full_name(emp) == 'Alice DUPONT'

    def test_with_spaces(self):
        emp = {'first_name': 'Jean Pierre', 'last_name': 'DE LA FONTAINE'}
        assert GameMode._make_full_name(emp) == 'Jean Pierre DE LA FONTAINE'


class TestGetNameChoices:
    def test_returns_correct_count(self, stub_mode):
        employees = stub_mode.game_manager.employee_data.get_all_employees()
        selected = employees[0]  # Alice DUPONT, woman
        choices = stub_mode._get_name_choices(selected, count=4)
        assert len(choices) == 4

    def test_includes_correct_name(self, stub_mode):
        employees = stub_mode.game_manager.employee_data.get_all_employees()
        selected = employees[0]  # Alice DUPONT, woman
        correct_name = f"{selected['first_name']} {selected['last_name']}"
        choices = stub_mode._get_name_choices(selected, count=4)
        assert correct_name in choices

    def test_filters_by_sex(self, stub_mode):
        employees = stub_mode.game_manager.employee_data.get_all_employees()
        # Pick a man
        men = [e for e in employees if e['sex'] == 'man']
        selected = men[0]
        choices = stub_mode._get_name_choices(selected, count=4)
        # All choices should be names of men from the dataset
        all_men = stub_mode.game_manager.employee_data.get_filtered_employees({'sex': 'man'})
        all_men_names = {f"{e['first_name']} {e['last_name']}" for e in all_men}
        for name in choices:
            assert name in all_men_names

    def test_fewer_employees_than_count(self, stub_mode):
        employees = stub_mode.game_manager.employee_data.get_all_employees()
        selected = employees[0]  # Alice DUPONT, woman
        # Request more than available women (5 women in test data)
        choices = stub_mode._get_name_choices(selected, count=10)
        assert len(choices) <= 10
        correct_name = f"{selected['first_name']} {selected['last_name']}"
        assert correct_name in choices


class TestPickNextEmployee:
    def test_returns_first_employee(self, stub_mode):
        game_data = stub_mode.game_manager.employee_data.get_all_employees()
        data_id = 42
        stub_mode.game_manager.get_game_data.return_value = game_data

        used = []
        emp, q = stub_mode._pick_next_employee(data_id, used, 0)
        assert emp == game_data[0]
        assert q == 1
        assert 0 in used

    def test_increments_question_counter(self, stub_mode):
        game_data = stub_mode.game_manager.employee_data.get_all_employees()
        data_id = 42
        stub_mode.game_manager.get_game_data.return_value = game_data

        used = [0]
        emp, q = stub_mode._pick_next_employee(data_id, used, 5)
        assert q == 6

    def test_game_over_when_all_used(self, stub_mode):
        game_data = stub_mode.game_manager.employee_data.get_all_employees()
        data_id = 42
        stub_mode.game_manager.get_game_data.return_value = game_data

        used = list(range(len(game_data)))
        result, q = stub_mode._pick_next_employee(data_id, used, len(game_data))
        assert result == {'game_over': True}

    def test_sequential_picks(self, stub_mode):
        game_data = stub_mode.game_manager.employee_data.get_all_employees()
        data_id = 42
        stub_mode.game_manager.get_game_data.return_value = game_data

        used = []
        picked_employees = []
        for i in range(len(game_data)):
            emp, q = stub_mode._pick_next_employee(data_id, used, i)
            picked_employees.append(emp)
        assert len(picked_employees) == len(game_data)
        # After all picked, game_over
        result, _ = stub_mode._pick_next_employee(data_id, used, len(game_data))
        assert result == {'game_over': True}


class TestInitialize:
    def test_returns_expected_keys(self, test_employee_data):
        gm = MagicMock()
        gm.employee_data = test_employee_data
        gm.score_manager.initialize_user.return_value = 123
        gm.store_game_data.return_value = 456
        mode = _StubMode(gm)

        employees = test_employee_data.get_all_employees()
        result = mode.initialize(user_id=123)
        assert result['user_id'] == 123
        assert result['data_id'] == 456
        assert result['max_score'] == len(employees)
        assert result['reverse_mode'] is False

    def test_calls_store_game_data(self, test_employee_data):
        gm = MagicMock()
        gm.employee_data = test_employee_data
        gm.score_manager.initialize_user.return_value = 1
        gm.store_game_data.return_value = 99
        mode = _StubMode(gm)

        mode.initialize()
        gm.store_game_data.assert_called_once()
