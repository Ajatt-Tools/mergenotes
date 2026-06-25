# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
from collections.abc import Iterable
from typing import Optional

from aqt.qt import *

from ..ajt_common.enum_select_combo import EnumSelectCombo
from ..config_types import OrderingChoice, SortOrder


class OrderingWidget(QWidget):
    """Combines the ordering combo and sort order combo into a single row."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Create the ordering and sort order combos."""
        super().__init__(parent)
        self._ordering_combo = EnumSelectCombo(enum_type=OrderingChoice, show_values=True)
        self._sort_order_combo = EnumSelectCombo(enum_type=SortOrder)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Arrange child widgets horizontally with zero margins."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self._ordering_combo)
        layout.addWidget(self._sort_order_combo)
        self.add_tooltips()

    @property
    def ordering_combo(self) -> QComboBox:
        """Return the ordering selection combo."""
        return self._ordering_combo

    def set_ordering_choice(self, ordering: OrderingChoice) -> None:
        """
        Set current ordering choice, e.g. "Due", "Interval length", "Card ID", "Deck ID", etc.
        """
        self._ordering_combo.setCurrentName(ordering)

    def current_ordering_choice(self) -> str:
        return self._ordering_combo.currentName()

    def add_tooltips(self) -> None:
        self._ordering_combo.setToolTip(
            "How to sort cards when merging.\nIf key is numeric, assume that the corresponding field contains a number."
        )
        self._sort_order_combo.setToolTip("Sort direction: ascending (default) or descending.")

    def current_sort_order(self) -> str:
        return self._sort_order_combo.currentName()

    def set_sort_order(self, sort_order: SortOrder) -> None:
        self._sort_order_combo.setCurrentName(sort_order)
