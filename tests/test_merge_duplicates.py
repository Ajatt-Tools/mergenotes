# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from collections.abc import Sequence
from typing import NamedTuple
from unittest.mock import create_autospec

import pytest
from anki.collection import Collection, OpChanges

from merge_notes.config_types import OriginalNotesAction, SortOrder
from merge_notes.merge_duplicates import MergeDupes, carefully_get_notes
from playground.no_anki_config import NoAnkiConfigView
from tests.helpers import FakeCard, FakeCollection, FakeNote


class MergeActionScenario(NamedTuple):
    """Describe how an original-note action selects merge recipients and handles the other notes."""

    action: OriginalNotesAction
    updated_indices: Sequence[int]
    removed_indices: Sequence[int]
    suspended_indices: Sequence[int]


class TestCarefullyGetNotes:
    """Verify filtering and deduplication without assuming an order for returned notes."""

    @pytest.mark.parametrize(
        "nids,has_field,expected_ids",
        [
            ([1, 2, 3], None, [1, 2, 3]),
            ([1, 999], None, [1]),
            ([999], None, []),
            ([1, 2], "Missing", []),
            ([1, 2, 3], "A", [1, 3]),
            ([1, 2, 3], "B", [2]),
            ([1, 1, 3], "A", [1, 3]),
            ([], None, []),
        ],
    )
    def test_filter(self, nids: Sequence[int], has_field: str | None, expected_ids: Sequence[int]) -> None:
        """Skip nonexistent and mismatched notes, returning each surviving note once."""
        col = FakeCollection([FakeNote(1, {"A": "x"}), FakeNote(2, {"B": "y"}), FakeNote(3, {"A": "z"})])
        assert sorted(note.id for note in carefully_get_notes(col, nids, has_field=has_field)) == expected_ids


class TestMergeDupes:
    """Exercise content, ordering, persistence, and independent duplicate groups."""

    @pytest.mark.parametrize("action", list(OriginalNotesAction))
    def test_empty_groups_rejected(self, no_anki_config: NoAnkiConfigView, action: OriginalNotesAction) -> None:
        """Reject an empty request before creating an undo entry or changing the collection."""
        no_anki_config["original_notes_action"] = action.name
        col = create_autospec(Collection, instance=True)
        with pytest.raises(AssertionError):
            MergeDupes(col, no_anki_config).op([])
        assert col.mock_calls == []

    @pytest.mark.parametrize(
        "sort_order,ordered_ids,merged",
        [(SortOrder.ascending, [1, 2], "one|two"), (SortOrder.descending, [2, 1], "two|one")],
    )
    @pytest.mark.parametrize(
        "scenario",
        [
            MergeActionScenario(
                action=OriginalNotesAction.delete, updated_indices=(1,), removed_indices=(0,), suspended_indices=()
            ),
            MergeActionScenario(
                action=OriginalNotesAction.do_nothing, updated_indices=(0, 1), removed_indices=(), suspended_indices=()
            ),
            MergeActionScenario(
                action=OriginalNotesAction.suspend, updated_indices=(1,), removed_indices=(), suspended_indices=(0,)
            ),
        ],
        ids=["delete", "do_nothing", "suspend"],
    )
    def test_merge_content(
        self,
        no_anki_config: NoAnkiConfigView,
        scenario: MergeActionScenario,
        sort_order: SortOrder,
        ordered_ids: Sequence[int],
        merged: str,
    ) -> None:
        """Merge in configured card order and persist exactly the intended recipients."""
        no_anki_config["original_notes_action"] = scenario.action.name
        no_anki_config["avoid_content_loss"] = False
        no_anki_config["ordering"] = "card_id"
        no_anki_config["sort_order"] = sort_order.name
        no_anki_config["field_separator"] = "|"
        col = FakeCollection([FakeNote(1, {"A": "one"}), FakeNote(2, {"A": "two"})])
        # Distinct sort keys and reversed input prevent a no-op sort from passing.
        result = MergeDupes(col, no_anki_config).op([("group", [2, 1])])
        assert [note.id for note in col.updated_notes] == [ordered_ids[index] for index in scenario.updated_indices]
        assert col.updated_notes[-1]["A"] == merged
        assert col.removed_note_ids == [ordered_ids[index] for index in scenario.removed_indices]
        assert col.sched.suspended_card_ids == [ordered_ids[index] * 10 for index in scenario.suspended_indices]
        assert result == OpChanges(note=True)

    @pytest.mark.parametrize(
        "groups,expected_ids,expected_fields",
        [
            ([("empty", [])], [], []),
            ([("single", [1])], [], []),
            ([("missing", [1, 999])], [], []),
            ([("repeated", [1, 1])], [], []),
            ([("pair", [1, 2, 999])], [1, 2], ["one", "one|two"]),
            ([("first", [1, 2]), ("second", [3, 4])], [1, 2, 3, 4], ["one", "one|two", "three", "three|four"]),
        ],
    )
    def test_groups(
        self,
        no_anki_config: NoAnkiConfigView,
        groups: list[tuple[str, list[int]]],
        expected_ids: Sequence[int],
        expected_fields: Sequence[str],
    ) -> None:
        """Ignore unmergeable groups and keep content from independent groups separate."""
        no_anki_config["ordering"] = "card_id"
        no_anki_config["original_notes_action"] = "do_nothing"
        no_anki_config["field_separator"] = "|"
        col = FakeCollection(
            [FakeNote(nid, {"A": text}) for nid, text in enumerate(["one", "two", "three", "four"], 1)]
        )
        assert MergeDupes(col, no_anki_config).op(groups) == OpChanges(note=True)
        assert [note.id for note in col.updated_notes] == expected_ids
        assert [note["A"] for note in col.updated_notes] == expected_fields
        assert col.removed_note_ids == []

    @pytest.mark.parametrize(
        "sort_order,groups,expected_cards",
        [
            (SortOrder.ascending, [("group", [1, 2])], [10, 11]),
            (SortOrder.descending, [("group", [1, 2])], [20, 21]),
            (SortOrder.ascending, [("first", [1, 2]), ("second", [3, 4])], [10, 11, 30, 31]),
            (SortOrder.descending, [("first", [1, 2]), ("second", [3, 4])], [20, 21, 40, 41]),
            (SortOrder.ascending, [("single", [1])], []),
            (SortOrder.ascending, [("missing", [1, 999])], []),
            (SortOrder.ascending, [("group", [1, 2, 999])], [10, 11]),
        ],
    )
    def test_suspend_originals(
        self,
        no_anki_config: NoAnkiConfigView,
        sort_order: SortOrder,
        groups: list[tuple[str, list[int]]],
        expected_cards: Sequence[int],
    ) -> None:
        """Suspend every original card across duplicate groups without suspending recipients or deleting notes."""
        no_anki_config["original_notes_action"] = "suspend"
        no_anki_config["ordering"] = "card_id"
        no_anki_config["sort_order"] = sort_order.name
        no_anki_config["avoid_content_loss"] = False
        col = FakeCollection(
            [FakeNote(nid, {"A": text}) for nid, text in enumerate(["one", "two", "three", "four"], 1)]
        )
        # Notes can generate several cards. All cards of each original must be suspended.
        for note in col.notes.values():
            note.cards().append(FakeCard(note.id * 10 + 1, note))
        MergeDupes(col, no_anki_config).op(groups)
        assert col.sched.suspended_card_ids == expected_cards
        assert col.removed_note_ids == []
