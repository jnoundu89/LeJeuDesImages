# models/game_mode.py
"""Abstract game mode + built-in Normal/Reverse modes + factory.

The base class exposes **declarative metadata** (``required_fields``,
``tags``, ``difficulty``, ``preview_type``, etc.) so the UI can render
cards without a mode-by-mode if/else, and an ``is_available()`` check
so modes whose required columns are missing in the active dataset get
greyed out automatically.

Behaviour hooks — ``_extra_init_data``, ``_parse_answer``,
``_session_updates_for`` — let subclasses customise initialisation
and form handling without re-implementing boilerplate, so a fix in
the base class propagates to every mode.
"""
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar, Dict, List, Optional, Sequence, Tuple, Union

from flask_babel import lazy_gettext as _l

from .game import GameManager


@dataclass
class AvailabilityCheck:
    """Result of :meth:`GameMode.is_available`.

    - ``available`` is True when the dataset has enough eligible employees.
    - ``missing_fields`` lists required columns that are empty for *all* rows.
    - ``eligible_count`` / ``min_eligible`` let the UI explain the gap.
    """
    available: bool
    eligible_count: int
    min_eligible: int
    required_fields: List[str] = field(default_factory=list)
    missing_fields: List[str] = field(default_factory=list)


class GameMode(ABC):
    """Abstract base class for game modes.

    Subclasses declare metadata via class attributes and implement
    ``get_question_data`` / ``update_score``. The default
    ``initialize`` and ``handle_answer`` cover every common case —
    override only the hooks you need.
    """

    # --- Declarative metadata (override in subclasses) ------------------
    #: Canonical fields every eligible employee must have populated.
    required_fields: ClassVar[List[str]] = ['photo', 'first_name', 'last_name']
    #: Minimum eligible employees before the mode becomes playable.
    min_eligible_employees: ClassVar[int] = 10
    #: 1 = easy, 2 = medium, 3 = hard.
    difficulty: ClassVar[int] = 2
    #: Rough play-time in seconds, shown on the mode card.
    estimated_duration_sec: ClassVar[int] = 120
    #: Free-form tags used by the mode-selection filter bar.
    tags: ClassVar[List[str]] = []
    #: Font Awesome icon class shown on the mode card.
    icon: ClassVar[str] = 'fa-gamepad'
    #: Preview component keyword; falls back to a static render when
    #: the front doesn't recognise the value.
    preview_type: ClassVar[str] = 'static'
    #: Max points per employee — used by modes that grant 2+ points per round.
    score_multiplier: ClassVar[int] = 1
    #: Whether the mode is still experimental / opt-in in the UI.
    experimental: ClassVar[bool] = False

    def __init__(self, game_manager: GameManager):
        self.game_manager = game_manager

    # --- Abstract interface ---------------------------------------------
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> Union[str, Any]:  # LazyString from flask_babel
        pass

    @property
    def display_name(self) -> Union[str, Any]:
        """Human-readable mode name (cards, menus, scoreboard).

        Default turns ``'emoji_challenge'`` into ``'Emoji Challenge'``;
        override in subclasses to return a translated ``_l(...)``.
        """
        return self.name.replace('_', ' ').title()

    @property
    @abstractmethod
    def template(self) -> str:
        pass

    @abstractmethod
    def get_question_data(self, data_id: int, used_indices: List[int],
                          current_question: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    def update_score(self, user_id: int, **kwargs) -> None:
        pass

    # --- Initialisation -------------------------------------------------
    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Default init: pick eligible employees, shuffle, store, return.

        Subclasses override :meth:`_extra_init_data` to add mode-specific
        keys (``time_limit``, etc.) rather than rewriting the boilerplate.
        """
        user_id = self.game_manager.score_manager.initialize_user(user_id, mode=self.name)
        employees = self._prepare_employees()
        data_id = self.game_manager.store_game_data(employees)
        result: Dict[str, Any] = {
            'user_id': user_id,
            'data_id': data_id,
            'max_score': len(employees) * self.score_multiplier,
        }
        result.update(self._extra_init_data(employees))
        return result

    def _prepare_employees(self) -> List[Dict[str, Any]]:
        """Return the shuffled, eligible employee list for this mode."""
        all_employees = self.game_manager.employee_data.get_all_employees()
        employees = self.eligible_employees(all_employees)
        random.shuffle(employees)
        return employees

    def _extra_init_data(self, employees: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Hook for subclasses to add keys to the initialize() dict."""
        return {}

    # --- Availability ---------------------------------------------------
    @classmethod
    def eligible_employees(cls, all_employees: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Employees with every required field populated (non-empty)."""
        return [e for e in all_employees if cls._has_all_required_fields(e)]

    @classmethod
    def _has_all_required_fields(cls, employee: Dict[str, Any]) -> bool:
        for field_name in cls.required_fields:
            value = employee.get(field_name)
            if value is None or (isinstance(value, str) and not value.strip()):
                return False
        return True

    def is_available(self) -> AvailabilityCheck:
        """Check whether the active dataset supplies enough data for this mode."""
        all_employees = self.game_manager.employee_data.get_all_employees()
        eligible = self.eligible_employees(all_employees)
        missing = self._globally_missing_fields(all_employees)
        return AvailabilityCheck(
            available=len(eligible) >= self.min_eligible_employees,
            eligible_count=len(eligible),
            min_eligible=self.min_eligible_employees,
            required_fields=list(self.required_fields),
            missing_fields=missing,
        )

    @classmethod
    def _globally_missing_fields(cls, all_employees: Sequence[Dict[str, Any]]) -> List[str]:
        """Required fields that are empty for *every* row (= column absent)."""
        if not all_employees:
            return list(cls.required_fields)
        missing = []
        for field_name in cls.required_fields:
            if not any(
                (e.get(field_name) and (not isinstance(e.get(field_name), str) or e[field_name].strip()))
                for e in all_employees
            ):
                missing.append(field_name)
        return missing

    # --- Answer handling ------------------------------------------------
    def handle_answer(self, user_id: int, form_data: dict, session_data: dict) -> dict:
        """Parse the submitted form, update the score, return session changes.

        Subclasses override :meth:`_parse_answer` (to read different form
        fields) and :meth:`_session_updates_for` (to mutate the session
        after a correct answer) instead of rewriting this method.
        """
        payload = self._parse_answer(form_data)
        self.update_score(user_id, **payload)
        return self._session_updates_for(payload, session_data)

    def _parse_answer(self, form_data: dict) -> dict:
        """Extract the score-relevant kwargs from the submitted form."""
        return {'correct_answer': int(form_data.get('correct_answer', 0))}

    def _session_updates_for(self, payload: dict, session_data: dict) -> dict:
        """Return session keys to update after handling the answer."""
        return {}

    # --- Shared helpers used by simple modes ----------------------------
    def _pick_next_employee(
        self,
        data_id: int,
        used_indices: List[int],
        current_question: int,
    ) -> Tuple[Dict[str, Any], int]:
        """Pick the next employee sequentially.

        Returns ``(employee, current_question)`` or
        ``({'game_over': True}, current_question)`` when done.
        """
        game_data = self.game_manager.get_game_data(data_id)

        if len(used_indices) >= len(game_data):
            return {'game_over': True}, current_question

        available_indices = [i for i in range(len(game_data)) if i not in used_indices]
        if not available_indices:
            return {'game_over': True}, current_question

        index = available_indices[0]
        used_indices.append(index)
        current_question += 1

        return game_data[index], current_question

    def _get_name_choices(
        self,
        selected_employee: Dict[str, Any],
        all_employees: Optional[List[Dict[str, Any]]] = None,
        count: int = 4,
    ) -> List[str]:
        """Return *count* full-name strings (1 correct + distractors), filtered by sex."""
        full_name = self._make_full_name(selected_employee)

        def _exclude_self(pool: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
            return [
                e for e in pool
                if e['first_name'] != selected_employee['first_name']
                or e['last_name'] != selected_employee['last_name']
            ]

        filtered_employees = self.game_manager.employee_data.get_filtered_employees(
            {'sex': selected_employee['sex']}
        )
        other_employees = _exclude_self(filtered_employees)

        needed = count - 1
        # Same robustness guard as `get_random_choices`: when the sex
        # filter doesn't yield enough distractors (mapping is wrong /
        # column is empty / column carries unique values), fall back
        # to every employee so the question still has multiple choices.
        if len(other_employees) < needed:
            other_employees = _exclude_self(
                self.game_manager.employee_data.get_all_employees()
            )

        if len(other_employees) >= needed:
            other_employees = random.sample(other_employees, needed)

        names = [full_name] + [self._make_full_name(e) for e in other_employees]
        random.shuffle(names)
        return names

    @staticmethod
    def _make_full_name(employee: Dict[str, Any]) -> str:
        return f"{employee['first_name']} {employee['last_name']}"


class NormalMode(GameMode):
    """Normal game mode: identify company, team, name, and position from an image."""

    required_fields: ClassVar[List[str]] = [
        'photo', 'first_name', 'last_name', 'team', 'job_title', 'company', 'sex',
    ]
    difficulty: ClassVar[int] = 2
    estimated_duration_sec: ClassVar[int] = 240
    tags: ClassVar[List[str]] = ['culture', 'photo', 'populaire']
    icon: ClassVar[str] = 'fa-user-tie'
    preview_type: ClassVar[str] = 'normal'
    score_multiplier: ClassVar[int] = 4

    @property
    def name(self) -> str:
        return 'normal'

    @property
    def display_name(self):
        return _l('Normal')

    @property
    def description(self):
        return _l("Identifiez l'entreprise, l'équipe, le nom et le poste de la personne sur l'image")

    @property
    def template(self) -> str:
        return 'normal.html'

    def get_question_data(self, data_id: int, used_indices: List[int],
                          current_question: int) -> Dict[str, Any]:
        selected, current_question = self._pick_next_employee(data_id, used_indices, current_question)
        if selected.get('game_over'):
            return selected

        correct_values = {
            'company': selected['company'],
            'team': selected['team'],
            'name': self._make_full_name(selected),
            'position': selected['job_title'],
        }

        companies = self.game_manager.employee_data.get_unique_values('company')
        teams = self.game_manager.employee_data.get_random_choices('team', correct_values['team'])
        names = self._get_name_choices(selected)
        sex_filter = {'sex': selected['sex']}
        positions = self.game_manager.employee_data.get_random_choices(
            'job_title', correct_values['position'], filter_dict=sex_filter
        )

        return {
            'game_over': False,
            'image_url': selected['photo'],
            'correct_values': correct_values,
            'choices': {
                'companies': companies,
                'teams': teams,
                'names': names,
                'positions': positions,
            },
            'current_question': current_question,
        }

    def update_score(self, user_id: int, **kwargs) -> None:
        score_increment = kwargs.get('score_increment', 0)
        stat_updates = {}
        for key in ('company', 'team', 'name', 'position'):
            val = kwargs.get(f'{key}_correct', 0)
            if val:
                stat_updates[key] = val
        self.game_manager.score_manager.update_score(user_id, score_increment, stat_updates=stat_updates)

    def _parse_answer(self, form_data: dict) -> dict:
        return {
            'score_increment': int(form_data.get('score_increment', 0)),
            'company_correct': int(form_data.get('company_correct', 0)),
            'team_correct': int(form_data.get('team_correct', 0)),
            'name_correct': int(form_data.get('name_correct', 0)),
            'position_correct': int(form_data.get('position_correct', 0)),
        }


class ReverseMode(GameMode):
    """Reverse game mode: identify the person from a name."""

    required_fields: ClassVar[List[str]] = ['photo', 'first_name', 'last_name', 'sex']
    difficulty: ClassVar[int] = 2
    estimated_duration_sec: ClassVar[int] = 150
    tags: ClassVar[List[str]] = ['culture', 'photo']
    icon: ClassVar[str] = 'fa-arrow-right-arrow-left'
    preview_type: ClassVar[str] = 'static'

    @property
    def name(self) -> str:
        return 'reverse'

    @property
    def display_name(self):
        return _l('Inverse')

    @property
    def description(self):
        return _l("Identifiez la personne correspondant au nom affiché")

    @property
    def template(self) -> str:
        return 'reverse.html'

    def get_question_data(self, data_id: int, used_indices: List[int],
                          current_question: int) -> Dict[str, Any]:
        selected, current_question = self._pick_next_employee(data_id, used_indices, current_question)
        if selected.get('game_over'):
            return selected

        correct_value = self._make_full_name(selected)
        sex_filter = {'sex': selected['sex']}
        filtered = self.game_manager.employee_data.get_filtered_employees(sex_filter)
        others = [e for e in filtered if self._make_full_name(e) != correct_value]
        if len(others) > 3:
            others = random.sample(others, 3)

        choices = [selected] + others
        random.shuffle(choices)

        return {
            'game_over': False,
            'correct_value': correct_value,
            'choices': choices,
            'current_question': current_question,
        }

    def update_score(self, user_id: int, **kwargs) -> None:
        if kwargs.get('correct_answer', 0):
            self.game_manager.score_manager.update_score(user_id, 1, stat_updates={'name': 1})
        else:
            self.game_manager.score_manager.update_score(user_id, 0)


class GameModeFactory:
    """Registers game mode instances and exposes them by name."""

    def __init__(self, game_manager: GameManager):
        self.game_manager = game_manager
        self.modes: Dict[str, GameMode] = {}

        # Register default game modes
        self.register_mode(NormalMode(game_manager))
        self.register_mode(ReverseMode(game_manager))

    def register_mode(self, mode: GameMode) -> None:
        self.modes[mode.name] = mode

    def get_mode(self, mode_name: str) -> Optional[GameMode]:
        return self.modes.get(mode_name)

    def get_all_modes(self) -> Dict[str, GameMode]:
        return self.modes
