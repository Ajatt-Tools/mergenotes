# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from collections.abc import Iterable

import anki.errors


class FakeCard:
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


class FakeNote:
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


class FakeScheduler:
    """Scheduler double that records suspended card IDs."""

    def __init__(self) -> None:
        """Initialize the recorded suspended card IDs."""
        self.suspended_card_ids: list[int] = []

    def suspend_cards(self, card_ids: list[int]) -> None:
        """Record card IDs requested for suspension."""
        self.suspended_card_ids.extend(card_ids)


class FakeCollection:
    """Collection double for MergeNotes tests."""

    def __init__(self, notes: Iterable[FakeNote] = ()) -> None:
        """Store notes and collection operation calls."""
        self.notes = {note.id: note for note in notes}
        self.sched = FakeScheduler()
        self.updated_notes: list[FakeNote] = []
        self.removed_note_ids: list[int] = []

    def add_custom_undo_entry(self, _action_name: str) -> int:
        """Return a fake undo position."""
        return 1

    def update_notes(self, notes: list[FakeNote]) -> None:
        """Record notes requested for update."""
        self.updated_notes.extend(notes)

    def remove_notes(self, note_ids: list[int]) -> None:
        """Record note IDs requested for removal."""
        self.removed_note_ids.extend(note_ids)

    def merge_undo_entries(self, _position: int) -> str:
        """Return a fake operation result."""
        return "changes"

    def get_note(self, note_id: int) -> FakeNote:
        """Return a note by ID, raising NotFoundError for missing notes."""
        if note_id not in self.notes:
            raise anki.errors.NotFoundError(message="", help_page="", context="", backtrace="")
        return self.notes[note_id]


class FakeSearchCollection(FakeCollection):
    """Collection double that supports duplicate-search operations."""

    def build_search_string(self, search: str, _node: object) -> str:
        """Return the search string unchanged."""
        return search

    def find_notes(self, query: str) -> list[int]:
        """Return all fake note IDs for any query."""
        return list(self.notes.keys())
