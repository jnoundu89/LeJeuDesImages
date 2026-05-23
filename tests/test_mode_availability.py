"""Tests for ``GameMode.is_available`` and ``eligible_employees``.

These gate the UI: a mode that needs ``birth_date`` should appear greyed
out when the active dataset has no such column, instead of crashing at
runtime.
"""
from unittest.mock import MagicMock

import pytest

from models.game_mode import AvailabilityCheck, GameMode


def _sample_employees(with_manager=True, with_birth_date=True, count=12):
    out = []
    for i in range(count):
        emp = {
            'first_name': f'F{i}',
            'last_name': f'L{i}',
            'photo': f'/p/{i}.jpg',
            'team': 'Engineering',
            'job_title': 'Engineer',
            'company': 'Corp',
            'sex': 'man' if i % 2 == 0 else 'woman',
        }
        if with_manager and i > 0:
            emp['manager_name'] = 'F0 L0'
        if with_birth_date:
            emp['birth_date'] = '1990-01-01'
        out.append(emp)
    return out


def _mode_with_employees(mode_factory, mode_name, employees):
    mode = mode_factory.get_mode(mode_name)
    if mode is None:
        pytest.skip(f'{mode_name} not registered')
    mock_data = MagicMock()
    mock_data.get_all_employees.return_value = employees
    mode.game_manager.employee_data = mock_data
    return mode


class TestEligibleEmployees:
    def test_filters_employees_missing_required_fields(self):
        class StrictMode(GameMode):
            required_fields = ['photo', 'first_name', 'last_name', 'manager_name']
            name = 'strict'  # type: ignore[assignment]
            description = 'strict test mode'  # type: ignore[assignment]
            template = 'strict.html'  # type: ignore[assignment]

            def get_question_data(self, *a, **k):
                return {}

            def update_score(self, *a, **k):
                pass

        employees = _sample_employees(with_manager=True)
        # First employee has no manager
        eligible = StrictMode.eligible_employees(employees)
        assert len(eligible) == 11  # 12 total, 1 has no manager

    def test_filters_empty_string_as_missing(self):
        class StrictMode(GameMode):
            required_fields = ['photo', 'first_name', 'last_name', 'manager_name']
            name = 'strict'  # type: ignore[assignment]
            description = 'strict test mode'  # type: ignore[assignment]
            template = 'strict.html'  # type: ignore[assignment]

            def get_question_data(self, *a, **k):
                return {}

            def update_score(self, *a, **k):
                pass

        employees = _sample_employees(count=3)
        employees[0]['manager_name'] = ''  # empty string counts as missing
        employees[1]['manager_name'] = '   '  # whitespace-only too
        employees[2]['manager_name'] = 'Valid'
        assert len(StrictMode.eligible_employees(employees)) == 1


class TestIsAvailable:
    """End-to-end availability check across registered modes."""

    def test_manager_mode_unavailable_when_no_manager_column(self, mode_factory):
        employees = _sample_employees(with_manager=False, count=12)
        mode = _mode_with_employees(mode_factory, 'manager', employees)
        check = mode.is_available()
        assert isinstance(check, AvailabilityCheck)
        assert check.available is False
        assert 'manager_name' in check.missing_fields
        assert check.eligible_count == 0

    def test_manager_mode_available_with_enough_eligible(self, mode_factory):
        employees = _sample_employees(with_manager=True, count=12)
        mode = _mode_with_employees(mode_factory, 'manager', employees)
        check = mode.is_available()
        # 11 have managers (first one doesn't), >= min_eligible=10
        assert check.available is True
        assert check.eligible_count == 11
        assert check.missing_fields == []

    def test_age_mode_unavailable_when_no_birth_date(self, mode_factory):
        employees = _sample_employees(with_birth_date=False, count=12)
        mode = _mode_with_employees(mode_factory, 'age', employees)
        check = mode.is_available()
        assert check.available is False
        assert 'birth_date' in check.missing_fields

    def test_mode_unavailable_below_min_eligible_threshold(self, mode_factory):
        employees = _sample_employees(count=5)  # below default min=10
        mode = _mode_with_employees(mode_factory, 'pixelation', employees)
        check = mode.is_available()
        assert check.available is False
        assert check.eligible_count == 5
        assert check.min_eligible == 10

    def test_check_exposes_required_fields(self, mode_factory):
        employees = _sample_employees(count=12)
        mode = _mode_with_employees(mode_factory, 'pixelation', employees)
        check = mode.is_available()
        assert set(check.required_fields) >= {'photo', 'first_name', 'last_name'}
