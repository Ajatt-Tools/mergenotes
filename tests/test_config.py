# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import sys

import pytest

from merge_notes.config import due_key, generic_numeric_key
from merge_notes.config_types import OrderingChoice, OriginalNotesAction, SortOrder
from playground.no_anki_config import NoAnkiConfigView
from tests.helpers import FakeCard


@pytest.mark.parametrize(
    "name, expected",
    [
        ("do_nothing", OriginalNotesAction.do_nothing),
        ("suspend", OriginalNotesAction.suspend),
        ("delete", OriginalNotesAction.delete),
    ],
)
def test_original_notes_action_members(name: str, expected: OriginalNotesAction) -> None:
    """Enum names resolve to the expected members."""
    assert OriginalNotesAction[name] is expected


@pytest.mark.parametrize(
    "name",
    [
        "",
        "remove",
        object(),
    ],
)
def test_original_notes_action_raises(name: str) -> None:
    """Enum names resolve to the expected members."""
    with pytest.raises(KeyError):
        _ = OriginalNotesAction[name]


@pytest.mark.parametrize(
    "value,expected",
    [
        ("do_nothing", OriginalNotesAction.do_nothing),
        ("suspend", OriginalNotesAction.suspend),
        ("delete", OriginalNotesAction.delete),
        ("bogus", OriginalNotesAction.do_nothing),
    ],
)
def test_original_notes_action_property(
    no_anki_config: NoAnkiConfigView, value: str, expected: OriginalNotesAction
) -> None:
    """The original_notes_action property handles valid and invalid config values."""
    no_anki_config["original_notes_action"] = value
    assert no_anki_config.original_notes_action is expected


@pytest.mark.parametrize(
    "value, expected",
    [
        ("due", OrderingChoice.due),
        ("card_id", OrderingChoice.card_id),
        ("bogus", OrderingChoice.due),
    ],
)
def test_ordering_property(no_anki_config: NoAnkiConfigView, value: str, expected: OrderingChoice) -> None:
    """The ordering property handles valid and invalid config values."""
    no_anki_config["ordering"] = value
    assert no_anki_config.ordering is expected


@pytest.mark.parametrize(
    "property_name, expected",
    [
        ("field_separator", "<br>"),
        ("merge_notes_shortcut", "Ctrl+Alt+M"),
        ("duplicate_notes_shortcut", "Ctrl+Alt+D"),
        ("sort_order", SortOrder.ascending),
        ("merge_tags", True),
        ("skip_if_not_empty", False),
        ("limit_to_fields", []),
        ("ordering", OrderingChoice.due),
        ("custom_sort_field", "SentAudio"),
        ("show_duplicate_notes_button", True),
        ("apply_when_searching_duplicates", True),
        ("ignore_html_tags", True),
        ("ignore_furigana", False),
        ("ignore_punctuation", True),
        ("full_width_as_half_width", True),
    ],
)
def test_config_properties(no_anki_config: NoAnkiConfigView, property_name: str, expected: object) -> None:
    """Config properties expose default config values."""
    assert getattr(no_anki_config, property_name) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        ("ascending", SortOrder.ascending),
        ("descending", SortOrder.descending),
        ("bogus", SortOrder.ascending),
    ],
)
def test_sort_order_property(no_anki_config: NoAnkiConfigView, value: str, expected: SortOrder) -> None:
    """The sort_order property handles valid and invalid config values."""
    no_anki_config["sort_order"] = value
    assert no_anki_config.sort_order is expected


def test_ordering_choices(no_anki_config: NoAnkiConfigView) -> None:
    """Config exposes all ordering choices used by the settings dialog."""
    assert list(no_anki_config.ordering_choices.keys()) == list(OrderingChoice)


@pytest.mark.parametrize(
    "card_type,due,expected",
    [
        (0, 5, (0, 5)),
        (2, 10, (2, 10)),
    ],
)
def test_due_key(card_type: int, due: int, expected: tuple[int, int]) -> None:
    """due_key returns a (type, due) tuple for sorting."""
    card = FakeCard(card_id=1, note=None, card_type=card_type, due=due)
    assert due_key(card) == expected


@pytest.mark.parametrize(
    "cmp_str,expected_first",
    [
        ("42", 42),
        ("abc", sys.maxsize),
    ],
)
def test_generic_numeric_key(cmp_str: str, expected_first: int) -> None:
    """generic_numeric_key returns numeric-first tuple, falling back to maxsize."""
    key_fn = generic_numeric_key(lambda _card: cmp_str)
    result = key_fn(None)
    assert result[0] == expected_first
    assert result[1] == cmp_str
