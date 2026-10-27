# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from collections.abc import Iterable, Sequence
from unittest.mock import create_autospec

import anki.errors
from anki.cards import Card
from anki.collection import Collection, OpChanges
from anki.notes import Note
from aqt.browser import Browser, Table
from aqt.browser.find_duplicates import FindDuplicatesDialog
from aqt.browser.table.model import DataModel
from aqt.forms import finddupes
from aqt.forms.browser import Ui_Dialog
from aqt.qt import QDialogButtonBox, QMenu, QTableView
from beartype import beartype

from merge_notes.ajt_common.restore_geom_dialog import AnkiSaveAndRestoreGeomDialog
from merge_notes.config_types import DueSortKey


@beartype
class GeometryDialog(AnkiSaveAndRestoreGeomDialog):
    """Supply a stable geometry key while exercising the real shared dialog constructor."""

    name = "merge_notes_geometry_test"


@beartype
def browser_with_cards_menu() -> Browser:
    """Build a browser double with a real Qt menu without opening an Anki collection."""
    browser = create_autospec(Browser, instance=True)
    browser.form = create_autospec(Ui_Dialog, instance=True)
    browser.form.menu_Cards = QMenu()
    return browser


@beartype
def table_for_selection(*, row: int | None, has_view: bool = True) -> Table:
    """Expose Anki's selection interfaces without initializing a collection or a browser window."""
    table = create_autospec(Table, instance=True)
    table.browser = create_autospec(Browser, instance=True)
    table._model = create_autospec(DataModel, instance=True)
    table._model.get_card_row.return_value = row
    table._view = None
    if has_view:
        table._view = create_autospec(QTableView, instance=True)
    return table


@beartype
def duplicate_search_dialog() -> FindDuplicatesDialog:
    """Provide a real Qt button box for exercising duplicate-report extensions without a webview."""
    dialog = create_autospec(FindDuplicatesDialog, instance=True)
    dialog.browser = create_autospec(Browser, instance=True)
    dialog.form = create_autospec(finddupes.Ui_Dialog, instance=True)
    dialog.form.buttonBox = QDialogButtonBox()
    return dialog


@beartype
def card_for_ordering(*, card_id: int, text: str, custom_text: str | None = None) -> Card:
    """Provide real Anki interfaces with distinct numeric and textual keys, without opening a collection."""
    fields = {"Expression": text}
    if custom_text is not None:
        fields["SentAudio"] = custom_text
    note = create_autospec(Note, instance=True)
    note.values.return_value = list(fields.values())
    note.note_type.return_value = {"sortf": 0}
    note.__contains__.side_effect = fields.__contains__
    note.__getitem__.side_effect = fields.__getitem__
    card = create_autospec(Card, instance=True)
    card.id = card_id
    card.due = card.ivl = 0
    card.did = 1
    card.type = 0
    card.note.return_value = note
    note.cards.return_value = [card]
    return card


@beartype
def cards_for_ordering_modes() -> Sequence[Card]:
    """Provide conflicting numeric orders so wiring one ordering mode to another cannot pass unnoticed."""
    cards = [
        card_for_ordering(card_id=3, text="abc", custom_text="20"),
        card_for_ordering(card_id=1, text="10", custom_text="2"),
        card_for_ordering(card_id=2, text="2", custom_text="10"),
    ]
    # A review card has the earliest due value but must still follow both new cards.
    for card, due_key, interval, deck_id in zip(
        cards,
        [DueSortKey(card_type=2, due=1), DueSortKey(card_type=0, due=30), DueSortKey(card_type=0, due=10)],
        [10, 20, 30],
        [20, 10, 30],
        strict=True,
    ):
        card.type, card.due = due_key
        card.ivl, card.did = interval, deck_id
    return cards


@beartype
class FakeCard(Card):
    """Small card double exposing only the fields used by merge tests."""

    def __init__(self, card_id: int, note: "FakeNote", card_type: int = 0, due: int = 0) -> None:
        """Store the card ID, owning note, and sort-relevant attributes."""
        self.id = card_id
        self._note = note
        self.type = card_type
        self.due = due

    def note(self) -> "FakeNote":
        """Return the note that owns this card."""
        return self._note


@beartype
class FakeNote(Note):
    """Small note double supporting field and tag operations."""

    def __init__(self, note_id: int, fields: dict[str, str], tags: Iterable[str] = ()) -> None:
        """Store field data and tags for tests."""
        self.id = note_id
        self._fields = dict(fields)
        self.tags = list(tags)
        # Each note owns one card. Card ID is note_id * 10 to avoid collisions.
        self._cards = [FakeCard(note_id * 10, self)]

    def __contains__(self, field_name: str) -> bool:
        """Return whether the note has a field."""
        return field_name in self._fields

    def __getitem__(self, field_name: str) -> str:
        """Return a field value."""
        return self._fields[field_name]

    def __setitem__(self, field_name: str, value: str) -> None:
        """Set a field value."""
        self._fields[field_name] = value

    def keys(self) -> list[str]:
        """Return field names."""
        return list(self._fields.keys())

    def has_tag(self, tag: str) -> bool:
        """Return whether the note already has a tag."""
        return tag in self.tags

    def add_tag(self, tag: str) -> None:
        """Add a tag to the note."""
        self.tags.append(tag)

    def cards(self) -> list[FakeCard]:
        """Return cards belonging to the note."""
        return self._cards


@beartype
class FakeScheduler:
    """Scheduler double that records suspended card IDs."""

    def __init__(self) -> None:
        """Initialize the recorded suspended card IDs."""
        self.suspended_card_ids: list[int] = []

    def suspend_cards(self, card_ids: list[int]) -> None:
        """Record card IDs requested for suspension."""
        self.suspended_card_ids.extend(card_ids)


@beartype
class FakeCollection(Collection):
    """Collection double for MergeNotes tests."""

    def __init__(self, notes: Iterable[FakeNote] = ()) -> None:
        """Store notes and collection operation calls."""
        # These in-memory subclasses expose the Anki types without opening a backend.
        # Their constructors initialize only the state exercised by the merge algorithms.
        self.notes = {note.id: note for note in notes}
        self.sched = FakeScheduler()
        self.updated_notes: list[FakeNote] = []
        self.removed_note_ids: list[int] = []

    def __del__(self) -> None:
        """Avoid closing an Anki backend because this double never opens one."""

    def add_custom_undo_entry(self, _action_name: str) -> int:
        """Return a fake undo position."""
        return 1

    def update_notes(self, notes: list[FakeNote]) -> None:
        """Record notes requested for update."""
        self.updated_notes.extend(notes)

    def remove_notes(self, note_ids: list[int]) -> None:
        """Record note IDs requested for removal."""
        self.removed_note_ids.extend(note_ids)

    def merge_undo_entries(self, _position: int) -> OpChanges:
        """Return an Anki-compatible operation result without invoking the backend."""
        return OpChanges(note=True)

    def get_note(self, note_id: int) -> FakeNote:
        """Return a note by ID, raising NotFoundError for missing notes."""
        if note_id not in self.notes:
            raise anki.errors.NotFoundError(message="", help_page="", context="", backtrace="")
        return self.notes[note_id]


@beartype
class FakeSearchCollection(FakeCollection):
    """Collection double that supports duplicate-search operations."""

    def build_search_string(self, search: str, _node: object) -> str:
        """Return the search string unchanged."""
        return search

    def find_notes(self, query: str) -> list[int]:
        """Return all fake note IDs for any query."""
        return list(self.notes.keys())
