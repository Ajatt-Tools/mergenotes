# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import os

import pytest
from aqt.qt import QApplication

from playground.no_anki_config import NoAnkiConfigView

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session", autouse=True)
def qapp() -> QApplication:
    """Ensure a QApplication exists for widget tests."""
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def no_anki_config() -> NoAnkiConfigView:
    """Return a mutable config view that does not require Anki."""
    return NoAnkiConfigView()
