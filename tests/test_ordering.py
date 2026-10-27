# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from collections.abc import Sequence
from unittest.mock import create_autospec

import pytest
from anki.notes import Note

from merge_notes.config import sort_field_key
from merge_notes.config_types import DueSortKey, NumericSortKey, OrderingChoice, SortKey
from merge_notes.merge_duplicates import MergeDupes
from playground.no_anki_config import NoAnkiConfigView
from tests.helpers import FakeCollection, card_for_ordering, cards_for_ordering_modes


class TestSortFieldKey:
    """Use the typed note-type lookup and do not confuse a missing type with an unsaved note."""

    @pytest.mark.parametrize("note_id", [0, 42])
    @pytest.mark.parametrize("sort_index,expected", [(0, "expression"), (1, "custom")])
    def test_note_type_sort_index(self, note_id: int, sort_index: int, expected: str) -> None:
        """Read the configured field index even when the note has not yet been assigned an ID."""
        card = card_for_ordering(card_id=1, text="expression", custom_text="custom")
        card.note().id = note_id
        card.note().note_type.return_value["sortf"] = sort_index
        assert sort_field_key(card) == expected

    @pytest.mark.parametrize("note_id", [0, 42])
    def test_missing_note_type(self, note_id: int) -> None:
        """Reject a missing note type regardless of whether the note already has an ID."""
        card = card_for_ordering(card_id=1, text="expression")
        card.note().id = note_id
        card.note().note_type.return_value = None
        with pytest.raises(AssertionError):
            sort_field_key(card)


class TestOrderingKeys:
    """Keep every configured key family comparable for both card and duplicate-note sorting."""

    @pytest.mark.parametrize("reverse", [False, True])
    @pytest.mark.parametrize(
        "ordering,minimum_key,expected_ids",
        [
            (OrderingChoice.due, DueSortKey(card_type=0, due=10), [2, 1, 3]),
            (OrderingChoice.interval_length, 10, [3, 1, 2]),
            (OrderingChoice.card_id, 1, [1, 2, 3]),
            (OrderingChoice.deck_id, 10, [1, 3, 2]),
            (OrderingChoice.sort_field, "10", [1, 2, 3]),
            (OrderingChoice.sort_field_numeric, NumericSortKey(number=2, text="2"), [2, 1, 3]),
            (OrderingChoice.custom_field, "10", [2, 1, 3]),
            (OrderingChoice.custom_field_numeric, NumericSortKey(number=2, text="2"), [1, 2, 3]),
        ],
    )
    def test_sort_notes(
        self,
        no_anki_config: NoAnkiConfigView,
        ordering: OrderingChoice,
        minimum_key: SortKey,
        expected_ids: Sequence[int],
        reverse: bool,
    ) -> None:
        """Choose the smallest card key for each note and preserve every mode's ordering in both directions."""
        no_anki_config["ordering"] = ordering.name
        cards = cards_for_ordering_modes()
        merger = MergeDupes(FakeCollection(), no_anki_config)
        multiple_cards = create_autospec(Note, instance=True)
        multiple_cards.cards.return_value = cards
        assert merger._sort_by_note_cards(multiple_cards) == minimum_key
        assert min(no_anki_config.ord_key(card) for card in cards) == minimum_key
        notes = [card.note() for card in cards]
        notes.sort(key=merger._sort_by_note_cards, reverse=reverse)
        if reverse:
            expected_ids = list(reversed(expected_ids))
        assert [note.cards()[0].id for note in notes] == expected_ids

    @pytest.mark.parametrize(
        "ordering,expected_ids",
        [(OrderingChoice.custom_field, [1, 2]), (OrderingChoice.custom_field_numeric, [2, 1])],
    )
    def test_missing_custom_field(
        self, no_anki_config: NoAnkiConfigView, ordering: OrderingChoice, expected_ids: Sequence[int]
    ) -> None:
        """Fall back to the note type's sort field when the configured custom field is absent."""
        no_anki_config["ordering"] = ordering.name
        cards = [card_for_ordering(card_id=2, text="2"), card_for_ordering(card_id=1, text="10")]
        assert [card.id for card in sorted(cards, key=no_anki_config.ord_key)] == expected_ids
