# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from collections.abc import Sequence
from unittest.mock import create_autospec

import pytest
from anki.collection import Collection, SearchNode

from merge_notes import find_duplicates
from merge_notes.find_duplicates import FindDuplicatesMenus, notes_from_search
from playground.no_anki_config import NoAnkiConfigView
from tests.helpers import FakeNote, FakeSearchCollection


class TestFindDuplicates:
    """Verify normalized grouping and selection of the configured search implementation."""

    @pytest.mark.parametrize(
        "values,expected",
        [
            (["<b>one!</b>", "one", "two"], [("one", [1, 2])]),
            (["one", "two", "one!", "two!", "one"], [("one", [1, 3, 5]), ("two", [2, 4])]),
            (["", " ", "!", "<b></b>"], []),
            (["x", "y", "z"], []),
            ([], []),
        ],
    )
    def test_deep_search(
        self, no_anki_config: NoAnkiConfigView, values: Sequence[str], expected: Sequence[tuple[str, list[int]]]
    ) -> None:
        """Group nonempty normalized values while omitting unique and empty values."""
        no_anki_config["punctuation_characters"] = "!"
        notes = [FakeNote(index, {"Expression": value}) for index, value in enumerate(values, start=1)]
        assert (
            FindDuplicatesMenus(no_anki_config)._deep_search_duplicates(FakeSearchCollection(notes), "Expression", "")
            == expected
        )

    @pytest.mark.parametrize("enabled,expected", [(True, [("one", [1, 2])]), (False, [("old", [9])])])
    def test_search_selection(
        self, no_anki_config: NoAnkiConfigView, enabled: bool, expected: Sequence[tuple[str, list[int]]]
    ) -> None:
        """Only call Anki's original search when enhanced comparison is disabled."""
        no_anki_config["apply_when_searching_duplicates"] = enabled
        col = FakeSearchCollection([FakeNote(1, {"Expression": "one"}), FakeNote(2, {"Expression": "one"})])
        old_search = create_autospec(Collection.find_dupes, return_value=[("old", [9])])
        result = FindDuplicatesMenus(no_anki_config).find_duplicates(col, "Expression", "tag:example", old_search)
        assert result == expected
        if enabled:
            old_search.assert_not_called()
        else:
            old_search.assert_called_once_with(col, "Expression", "tag:example")

    @pytest.mark.parametrize("search", ["", "tag:example"])
    def test_query_forwarding(self, monkeypatch: pytest.MonkeyPatch, search: str) -> None:
        """Delegate query construction to Anki and preserve the field filter during loading."""
        col = create_autospec(Collection, instance=True)
        col.build_search_string.return_value = "constructed query"
        col.find_notes.return_value = [1, 2]
        load = create_autospec(find_duplicates.carefully_get_notes, return_value=[])
        monkeypatch.setattr(find_duplicates, "carefully_get_notes", load)
        assert list(notes_from_search(col, "Expression", search)) == []
        col.build_search_string.assert_called_once_with(search, SearchNode(field_name="Expression"))
        col.find_notes.assert_called_once_with(query="constructed query")
        load.assert_called_once_with(col, [1, 2], has_field="Expression")
