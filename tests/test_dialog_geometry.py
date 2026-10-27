# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from unittest.mock import create_autospec

import pytest
from aqt import AnkiQt
from aqt.profiles import ProfileManager

from merge_notes.ajt_common import restore_geom_dialog
from tests.helpers import GeometryDialog


class TestDialogGeometry:
    """Guard profile access and preserve geometry through the real Qt dialog lifecycle."""

    @pytest.mark.parametrize("profile,expected", [(None, False), ({}, False), ({"name": "test"}, True)])
    def test_profile_guard(
        self, monkeypatch: pytest.MonkeyPatch, profile: dict[str, str] | None, expected: bool
    ) -> None:
        """Skip geometry storage outside Anki or before a nonempty profile has been loaded."""
        main = None
        if profile is not None:
            main = create_autospec(AnkiQt, instance=True)
            main.pm = create_autospec(ProfileManager, instance=True)
            main.pm.profile = profile
        monkeypatch.setattr(restore_geom_dialog, "mw", main)
        assert restore_geom_dialog.can_access_geom_data() is expected

    @pytest.mark.parametrize("available", [False, True])
    @pytest.mark.parametrize(
        "operation,restores,saves", [("show", True, False), ("accept", False, True), ("reject", False, True)]
    )
    def test_lifecycle(
        self, monkeypatch: pytest.MonkeyPatch, available: bool, operation: str, restores: bool, saves: bool
    ) -> None:
        """Restore on show and save on acceptance or rejection only when a profile is accessible."""
        dialog = GeometryDialog()
        restore = create_autospec(restore_geom_dialog.restoreGeom)
        save = create_autospec(restore_geom_dialog.saveGeom)
        # Restore the real helpers before closing the dialog triggers its final geometry save.
        with monkeypatch.context() as context:
            context.setattr(restore_geom_dialog, "can_access_geom_data", lambda: available)
            context.setattr(restore_geom_dialog, "restoreGeom", restore)
            context.setattr(restore_geom_dialog, "saveGeom", save)
            getattr(dialog, operation)()
        if available and restores:
            restore.assert_called_once_with(dialog, dialog.name, adjustSize=True)
        else:
            restore.assert_not_called()
        if available and saves:
            save.assert_called_once_with(dialog, dialog.name)
        else:
            save.assert_not_called()
        dialog.close()
