# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import json
import pathlib

import pytest

from merge_notes.config_types import OriginalNotesAction
from merge_notes.settings_dialog import MergeFieldsSettingsWindow, uniq_char_str
from playground.no_anki_config import NoAnkiConfigView

_CONFIG_JSON = json.loads(pathlib.Path("merge_notes/config.json").read_text(encoding="utf-8"))
_BOOL_KEYS = [k for k, v in _CONFIG_JSON.items() if isinstance(v, bool)]


@pytest.mark.parametrize(
    "text,expected_chars",
    [
        ("aabb", "ab"),
        ("", ""),
        ("hello", "helo"),
    ],
)
def test_uniq_char_str(text: str, expected_chars: str) -> None:
    """Duplicate characters are removed from a string."""
    assert uniq_char_str(text) == expected_chars


@pytest.mark.parametrize(
    "action_name",
    [
        OriginalNotesAction.do_nothing.name,
        OriginalNotesAction.suspend.name,
        OriginalNotesAction.delete.name,
    ],
)
def test_settings_dialog_loads_original_notes_action(no_anki_config: NoAnkiConfigView, action_name: str) -> None:
    """The original notes action combo loads the configured value."""
    no_anki_config["original_notes_action"] = action_name
    dialog = MergeFieldsSettingsWindow(no_anki_config)
    assert dialog._original_notes_action_combo.currentName() == action_name


@pytest.mark.parametrize(
    "separator, action",
    [
        (" | ", OriginalNotesAction.delete),
        ("\n", OriginalNotesAction.suspend),
        ("", OriginalNotesAction.do_nothing),
    ],
)
def test_settings_dialog_accept_saves_config(
    no_anki_config: NoAnkiConfigView,
    separator: str,
    action: OriginalNotesAction,
) -> None:
    """Accepting the dialog writes widget values back to config."""
    dialog = MergeFieldsSettingsWindow(no_anki_config)
    dialog._field_separator_edit.setText(separator)
    dialog._original_notes_action_combo.setCurrentName(action)

    dialog.accept()

    assert no_anki_config.field_separator == separator
    assert no_anki_config.original_notes_action is action
