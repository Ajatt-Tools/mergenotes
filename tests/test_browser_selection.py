# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import pytest
from anki.cards import CardId

from merge_notes.merge_notes import select_card
from tests.helpers import table_for_selection


class TestSelectCard:
    """Restore browser selection without touching an incompletely initialized table."""

    @pytest.mark.parametrize("row", [0, 3, None])
    def test_initialized_view(self, row: int | None) -> None:
        """Select and scroll to surviving rows, or notify the browser when the card has disappeared."""
        table = table_for_selection(row=row)
        select_card(table, CardId(42))
        table._reset_selection.assert_called_once_with()
        table._model.get_card_row.assert_called_once_with(CardId(42))
        if row is None:
            table._view.selectRow.assert_not_called()
            table._scroll_to_row.assert_not_called()
            table.browser.on_all_or_selected_rows_changed.assert_called_once_with()
            table.browser.on_current_row_changed.assert_called_once_with()
        else:
            table._view.selectRow.assert_called_once_with(row)
            table._scroll_to_row.assert_called_once_with(row, scroll_even_if_visible=False)
            table.browser.on_all_or_selected_rows_changed.assert_not_called()
            table.browser.on_current_row_changed.assert_not_called()

    @pytest.mark.parametrize("row", [0, None])
    def test_missing_view(self, row: int | None) -> None:
        """Leave selection and model state untouched when the table has no attached view."""
        table = table_for_selection(row=row, has_view=False)
        select_card(table, CardId(42))
        assert table.mock_calls == []
