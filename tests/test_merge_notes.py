# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import typing

import pytest

from merge_notes.config_types import OriginalNotesAction, SortOrder
from merge_notes.merge_notes import (
    MergeNotes,
    interpret_special_chars,
    merge_tags,
    notes_by_cards,
    pairs,
    reorder_by_common_fields,
)
from playground.no_anki_config import NoAnkiConfigView
from tests.helpers import FakeCollection, FakeNote


@pytest.mark.parametrize(
    "items,expected",
    [
        ([1, 2, 3], [(1, 2), (2, 3)]),
        ([1], []),
        ([], []),
    ],
)
def test_pairs(items: list[int], expected: list[tuple[int, int]]) -> None:
    """Adjacent pairs are generated from a sequence."""
    assert list(pairs(items)) == expected


@pytest.mark.parametrize(
    "cards_note_ids,expected_note_ids",
    [
        ([1, 2, 1], [1, 2]),
        ([1], [1]),
        ([], []),
    ],
)
def test_notes_by_cards(cards_note_ids: list[int], expected_note_ids: list[int]) -> None:
    """Cards are converted to unique notes in first-seen order."""
    notes = {nid: FakeNote(nid, {"A": "x"}) for nid in set(cards_note_ids)}
    cards = [notes[nid].cards()[0] for nid in cards_note_ids]
    result = notes_by_cards(typing.cast(cards))
    assert [note.id for note in result] == expected_note_ids


@pytest.mark.parametrize(
    "fields_a,fields_b,expect_a_first",
    [
        ({"A": "x"}, {"A": "x", "B": "y"}, True),
        ({"A": "x", "B": "y"}, {"A": "x"}, False),
        # Equal field count: stable sort preserves input order ([note_b, note_a])
        ({"A": "x"}, {"A": "x"}, False),
    ],
)
def test_reorder_by_common_fields(fields_a: dict[str, str], fields_b: dict[str, str], expect_a_first: bool) -> None:
    """Notes with fewer shared fields sort before notes with more fields."""
    note_a = FakeNote(1, fields_a)
    note_b = FakeNote(2, fields_b)
    result = reorder_by_common_fields([note_b, note_a])
    first_is_a = result[0] is note_a
    assert first_is_a is expect_a_first


@pytest.mark.parametrize(
    "source_tags,expected_tags",
    [
        (["leech"], ["target"]),
        (["marked"], ["target", "marked"]),
        (["target"], ["target"]),
        ([], ["target"]),
    ],
)
def test_merge_tags_excludes_leech(source_tags: list[str], expected_tags: list[str]) -> None:
    """Leech tags are never merged into the recipient."""
    recipient = FakeNote(1, {"A": "x"}, tags=["target"])
    source = FakeNote(2, {"A": "y"}, tags=source_tags)
    merge_tags(recipient, [source])
    assert recipient.tags == expected_tags


@pytest.mark.parametrize(
    "text,expected",
    [
        (r"line1\nline2", "line1\nline2"),
        (r"col1\tcol2", "col1\tcol2"),
        (r"line1\rline2", "line1\rline2"),
        ("plain text", "plain text"),
    ],
)
def test_interpret_special_chars(text: str, expected: str) -> None:
    """Escape sequences are converted to actual characters."""
    assert interpret_special_chars(text) == expected


@pytest.mark.parametrize(
    "config_overrides,source_fields,recipient_fields,separator,expected_fields",
    [
        # Merge fields and tags
        (
            {},
            {"A": "first", "B": ""},
            {"A": "second", "B": "target"},
            "|",
            {"A": "first|second", "B": "target"},
        ),
        # skip_if_not_empty
        (
            {"skip_if_not_empty": True},
            {"A": "first"},
            {"A": "second"},
            "|",
            {"A": "second"},
        ),
        # limit_to_fields
        (
            {"limit_to_fields": ["A"]},
            {"A": "first", "B": "source"},
            {"A": "second", "B": "target"},
            "|",
            {"A": "first|second", "B": "target"},
        ),
        # Different separator
        (
            {},
            {"A": "first"},
            {"A": "second"},
            " + ",
            {"A": "first + second"},
        ),
    ],
)
def test_merge_field_content(
    no_anki_config: NoAnkiConfigView,
    config_overrides: dict[str, object],
    source_fields: dict[str, str],
    recipient_fields: dict[str, str],
    separator: str,
    expected_fields: dict[str, str],
) -> None:
    """Field content is merged according to config flags."""
    for key, value in config_overrides.items():
        no_anki_config[key] = value
    source = FakeNote(1, source_fields, tags=["source"])
    recipient = FakeNote(2, recipient_fields, tags=["target"])
    merger = MergeNotes(FakeCollection([source, recipient]), no_anki_config)

    merger._merge_field_content(recipient, [source, recipient], separator)

    for field_name, expected_value in expected_fields.items():
        assert recipient[field_name] == expected_value


@pytest.mark.parametrize(
    "action,removed,suspended,updated_ids",
    [
        (OriginalNotesAction.do_nothing, [], [], [1, 2, 3]),
        (OriginalNotesAction.delete, [1, 2], [], [3]),
        (OriginalNotesAction.suspend, [], [1, 2], [3]),
    ],
)
def test_do_merge_original_notes_actions(
    no_anki_config: NoAnkiConfigView,
    action: OriginalNotesAction,
    removed: list[int],
    suspended: list[int],
    updated_ids: list[int],
) -> None:
    """The configured original-notes action selects the expected merge strategy."""
    no_anki_config["original_notes_action"] = action.name
    no_anki_config["avoid_content_loss"] = False
    notes = [
        FakeNote(1, {"A": "one"}),
        FakeNote(2, {"A": "two"}),
        FakeNote(3, {"A": "three"}),
    ]
    merger = MergeNotes(FakeCollection(notes), no_anki_config)

    merger._do_merge(notes)

    assert merger.nids_to_remove == removed
    assert merger.nids_to_suspend == suspended
    assert [note.id for note in merger.notes_to_update] == updated_ids


@pytest.mark.parametrize(
    "sort_order,expect_updated_id",
    [
        (SortOrder.ascending, 3),
        (SortOrder.descending, 1),
    ],
)
def test_do_merge_sort_order_reverses_target(
    no_anki_config: NoAnkiConfigView, sort_order: SortOrder, expect_updated_id: int
) -> None:
    """Descending sort order reverses which note receives merged content."""
    no_anki_config["original_notes_action"] = OriginalNotesAction.delete.name
    no_anki_config["avoid_content_loss"] = False
    no_anki_config["sort_order"] = sort_order.name
    notes = [
        FakeNote(1, {"A": "one"}),
        FakeNote(2, {"A": "two"}),
        FakeNote(3, {"A": "three"}),
    ]
    # Sort by card ID (ascending: 10, 20, 30 → note 3 is last → merge target).
    # Descending: 30, 20, 10 → note 1 is last → merge target.
    merger = MergeNotes(FakeCollection(notes), no_anki_config)
    sorted_notes = sorted(notes, key=lambda n: n.cards()[0].id, reverse=sort_order is SortOrder.descending)
    merger._do_merge(sorted_notes)

    assert merger.notes_to_update[0].id == expect_updated_id


@pytest.mark.parametrize(
    "action,expect_removed,expect_suspended,expect_updated",
    [
        (OriginalNotesAction.do_nothing, [], [], [1, 2]),
        (OriginalNotesAction.delete, [1], [], [2]),
        (OriginalNotesAction.suspend, [], [1], [2]),
    ],
)
def test_op_executes_full_merge_flow(
    no_anki_config: NoAnkiConfigView,
    action: OriginalNotesAction,
    expect_removed: list[int],
    expect_suspended: list[int],
    expect_updated: list[int],
) -> None:
    """op() merges, updates, removes/suspends, and returns changes."""
    no_anki_config["original_notes_action"] = action.name
    no_anki_config["avoid_content_loss"] = False
    notes = [FakeNote(1, {"A": "one"}), FakeNote(2, {"A": "two"})]
    col = FakeCollection(notes)

    MergeNotes(col, no_anki_config).op(notes)

    assert col.removed_note_ids == expect_removed
    assert col.sched.suspended_card_ids == [nid * 10 for nid in expect_suspended]
    assert [note.id for note in col.updated_notes] == expect_updated


@pytest.mark.parametrize(
    "note_ids,expected_card_ids",
    [
        ([1, 2], [10, 20]),
        ([1], [10]),
        ([], []),
    ],
)
def test_suspend_cards_of_notes(
    no_anki_config: NoAnkiConfigView, note_ids: list[int], expected_card_ids: list[int]
) -> None:
    """Suspending notes suspends all cards belonging to collected note IDs."""
    notes = [FakeNote(nid, {"A": "x"}) for nid in note_ids]
    col = FakeCollection(notes)
    merger = MergeNotes(col, no_anki_config)
    merger.nids_to_suspend.extend(note_ids)

    merger._suspend_cards_of_notes()

    assert col.sched.suspended_card_ids == expected_card_ids
