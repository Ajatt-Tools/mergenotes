# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import os
from collections.abc import Iterator, Sequence
from unittest.mock import create_autospec

import pytest
from aqt.qt import QApplication, QWidget
from beartype import beartype

from merge_notes.ajt_common import addon_config
from merge_notes.ajt_common.about_menu import AboutDialog
from playground.no_anki_config import NoAnkiConfigView


@beartype
def pytest_collection_modifyitems(items: Sequence[pytest.Item]) -> None:
    """Runtime-check collected test functions, including bound methods and parametrized cases.

    Adapted from Lancet. Non-function items must remain untouched.
    https://github.com/Ajatt-Tools/lancet/blob/a306fd1774f2b3a70a0f836bab1135d66f4741f2/tests/conftest.py#L11-L18
    """
    for item in items:
        if isinstance(item, pytest.Function):
            item.obj = beartype(item.obj)


@pytest.fixture(scope="session", autouse=True)
def qt_offscreen_platform() -> None:
    """
    Default to offscreen Qt in headless CI, preserving an explicitly selected platform.
    https://github.com/Ajatt-Tools/lancet/blob/a306fd1774f2b3a70a0f836bab1135d66f4741f2/tests/conftest.py#L22
    """
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session", autouse=True)
def qapp(qt_offscreen_platform: None) -> QApplication:
    """Ensure a QApplication exists for widget tests.

    A program name must be present in argv because QtWebEngine aborts
    when QApplication is created with an empty argument list.

    https://github.com/Ajatt-Tools/lancet/blob/a306fd1774f2b3a70a0f836bab1135d66f4741f2/tests/conftest.py#L28
    """
    match instance := QApplication.instance():
        case None:
            return QApplication(["pytest"])  # argv can't be empty
        case QApplication():
            return instance
        case _:
            raise RuntimeError("A QCoreApplication already exists. Widget tests require QApplication")


@pytest.fixture()
def no_anki_config() -> NoAnkiConfigView:
    """Return a mutable config view that does not require Anki."""
    return NoAnkiConfigView()


@pytest.fixture()
def config_backend(no_anki_config: NoAnkiConfigView, monkeypatch: pytest.MonkeyPatch) -> None:
    """Supply real config data without requiring an Anki main window or writing profile files."""
    monkeypatch.setattr(addon_config, "get_default_config", lambda: no_anki_config.default_config)
    monkeypatch.setattr(addon_config, "get_config", lambda: no_anki_config.config)


@pytest.fixture()
def about_dialog(monkeypatch: pytest.MonkeyPatch) -> Iterator[AboutDialog]:
    """Construct the real dialog while replacing only its unrelated QtWebEngine content."""
    parent = QWidget()
    webview = create_autospec(AboutDialog.make_about_webview, return_value=QWidget())
    with monkeypatch.context() as context:
        context.setattr(AboutDialog, "make_about_webview", webview)
        dialog = AboutDialog(parent)
        yield dialog
        dialog.close()
        parent.close()
