# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from unittest.mock import create_autospec

import pytest
from anki.notes import NoteId
from aqt import AnkiQt
from aqt.browser.find_duplicates import FindDuplicatesDialog

from merge_notes import merge_duplicates
from merge_notes.merge_duplicates import MergeDupes, MergeDuplicatesMenus
from playground.no_anki_config import NoAnkiConfigView
from tests.helpers import duplicate_search_dialog


class TestDuplicateReport:
    """Preserve Anki's report-wrapping convention and the dynamically attached merge button."""

    @pytest.mark.parametrize("checked", [False, True])
    def test_reuse_button(
        self, monkeypatch: pytest.MonkeyPatch, no_anki_config: NoAnkiConfigView, checked: bool
    ) -> None:
        """Reuse one button and discard clicked's checked flag while forwarding the latest report groups.

        https://doc.qt.io/qt-6/qabstractbutton.html#clicked
        """
        dialog = duplicate_search_dialog()
        menus = MergeDuplicatesMenus(no_anki_config)
        merge = create_autospec(menus._merge_dupes)
        monkeypatch.setattr(menus, "_merge_dupes", merge)
        menus.append_merge_duplicates_button(dialog, [("old", [NoteId(1), NoteId(2)])])
        groups = [("new", [NoteId(3), NoteId(4)])]
        menus.append_merge_duplicates_button(dialog, groups)
        buttons = dialog.form.buttonBox.buttons()
        assert len(buttons) == 1
        assert getattr(dialog, "_merge_dupes_button") is buttons[0]
        assert buttons[0].text() == MergeDupes.action_name
        buttons[0].clicked.emit(checked)
        merge.assert_called_once_with(parent=dialog.browser, dupes=groups)

    @pytest.mark.parametrize("groups", [[], [("group", [NoteId(1), NoteId(2)])]])
    def test_init_wraps_report(
        self, monkeypatch: pytest.MonkeyPatch, no_anki_config: NoAnkiConfigView, groups: list[tuple[str, list[NoteId]]]
    ) -> None:
        """Keep the original report method and invoke the add-on extension through Anki's real wrapper."""
        original = create_autospec(FindDuplicatesDialog.show_duplicates_report)
        append = create_autospec(MergeDuplicatesMenus.append_merge_duplicates_button)
        monkeypatch.setattr(FindDuplicatesDialog, "show_duplicates_report", original)
        monkeypatch.setattr(MergeDuplicatesMenus, "append_merge_duplicates_button", append)
        monkeypatch.setattr(merge_duplicates, "get_global_config", lambda: no_anki_config)
        monkeypatch.setattr(merge_duplicates, "mw", create_autospec(AnkiQt, instance=True))
        merge_duplicates.init()
        dialog = duplicate_search_dialog()
        FindDuplicatesDialog.show_duplicates_report(dialog, groups)
        original.assert_called_once_with(dialog, groups)
        menus = append.call_args.args[0]
        assert isinstance(menus, MergeDuplicatesMenus)
        append.assert_called_once_with(menus, dialog, groups)
