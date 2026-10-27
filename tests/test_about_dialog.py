# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from unittest.mock import create_autospec

import pytest
from aqt.qt import QDialog, QPushButton, QSize, QWidget

from merge_notes.ajt_common import about_menu
from merge_notes.ajt_common.about_menu import AboutDialog
from merge_notes.ajt_common.consts import (
    BUTTON_HEIGHT,
    COMMUNITY_LINK,
    DONATE_LINK,
    ICON_SIDE_LEN,
)


class TestAboutButtons:
    """Exercise the named button factories and their real Qt signal adapters."""

    @pytest.mark.parametrize("label,link", [("Join our community", COMMUNITY_LINK), ("Donate", DONATE_LINK)])
    def test_link_buttons(
        self, monkeypatch: pytest.MonkeyPatch, about_dialog: AboutDialog, label: str, link: str
    ) -> None:
        """Keep link destinations, icons, and dimensions consistent after extracting shared construction."""
        button = next(button for button in about_dialog.findChildren(QPushButton) if button.text() == label)
        assert button.height() == BUTTON_HEIGHT
        assert button.iconSize() == QSize(ICON_SIDE_LEN, ICON_SIDE_LEN)
        assert button.icon().isNull() is False
        open_link = create_autospec(about_menu.openLink)
        monkeypatch.setattr(about_menu, "openLink", open_link)
        button.click()
        open_link.assert_called_once_with(link)

    @pytest.mark.parametrize("checked", [False, True])
    def test_accept_button(self, monkeypatch: pytest.MonkeyPatch, about_dialog: AboutDialog, checked: bool) -> None:
        """Discard clicked's checked flag before invoking the geometry-aware accept method.

        https://doc.qt.io/qt-6/qabstractbutton.html#clicked
        """
        button = next(button for button in about_dialog.findChildren(QPushButton) if button.text() == "Ok")
        save = create_autospec(about_dialog._save_geom)
        with monkeypatch.context() as context:
            context.setattr(about_dialog, "_save_geom", save)
            button.clicked.emit(checked)
        save.assert_called_once_with()
        assert about_dialog.result() == QDialog.DialogCode.Accepted

    @pytest.mark.parametrize("checked", [False, True])
    def test_menu_action(self, monkeypatch: pytest.MonkeyPatch, checked: bool) -> None:
        """Discard triggered's checked flag before constructing and opening the modal dialog.

        https://doc.qt.io/qt-6/qaction.html#triggered
        """
        parent = QWidget()
        dialog = create_autospec(AboutDialog)
        dialog.return_value.exec.return_value = 0
        monkeypatch.setattr(about_menu, "AboutDialog", dialog)
        action = about_menu.create_about_action(parent)
        action.triggered.emit(checked)
        dialog.assert_called_once_with(None)
        dialog.return_value.exec.assert_called_once_with()
