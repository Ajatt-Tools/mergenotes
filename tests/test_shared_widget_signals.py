# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from collections.abc import Sequence

import pytest
from PyQt6.QtTest import QSignalSpy

from merge_notes.ajt_common.checkable_combobox import CheckableComboBox
from merge_notes.ajt_common.color_picker import ColorEditPicker


class TestSharedWidgetSignals:
    """Exercise signal adapters with real Qt model and text-change notifications."""

    @pytest.mark.parametrize("checked,expected", [([], ""), (["one"], "one"), (["one", "two"], "one, two")])
    def test_model_change(self, checked: Sequence[str], expected: str) -> None:
        """Discard model indices and roles before refreshing the combo's display text.

        https://doc.qt.io/qt-6/qabstractitemmodel.html#dataChanged
        """
        combo = CheckableComboBox()
        combo.setCheckableTexts(["one", "two"])
        # Seed a selection so the empty case also causes a real model state change.
        combo.setCheckedTexts(["two"])
        combo.setCheckedTexts(checked)
        assert combo.lineEdit().text() == expected

    @pytest.mark.parametrize("color", ["red", "#AABBCC"])
    def test_color_forwarding(self, color: str) -> None:
        """Forward the new text argument unchanged through color_changed.

        https://doc.qt.io/qt-6/qlineedit.html#textChanged
        """
        picker = ColorEditPicker("black")
        changes = QSignalSpy(picker.color_changed)
        picker.set_color(color)
        assert picker.color_hex() == color
        assert list(changes) == [[color]]
