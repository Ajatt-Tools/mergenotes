# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import pytest

from merge_notes.ajt_common.grab_key import KeyPressDialog, ShortCutGrabButton


class TestShortcutDefaults:
    """Preserve optional shortcut initialization when runtime type checking is enabled."""

    @pytest.mark.parametrize("initial", [None, "", "Ctrl+Alt+D"])
    def test_dialog(self, initial: str | None) -> None:
        """Accept both an unassigned shortcut and an explicit shortcut without coercing the value."""
        dialog = KeyPressDialog(initial_value=initial)
        assert dialog.value() == initial

    @pytest.mark.parametrize("initial,expected", [(None, ""), ("", ""), ("Ctrl+Alt+D", "Ctrl+Alt+D")])
    def test_button(self, initial: str | None, expected: str) -> None:
        """Expose unassigned shortcuts as empty strings while keeping the placeholder visible."""
        button = ShortCutGrabButton(initial)
        assert button.value() == expected
        if not expected:
            assert button.text() == "[Not assigned]"
