# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from typing import Optional

from aqt.qt import *


class KeyPressDialog(QDialog):
    MOD_MASK = Qt.CTRL | Qt.ALT | Qt.SHIFT | Qt.META
    value_accepted = pyqtSignal(str)

    def __init__(self, parent: QWidget = None, initial_value: str = None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self._shortcut = initial_value
        self.setMinimumSize(380, 64)
        self.setWindowTitle("Grab key combination")
        self.setLayout(self._make_layout())

    @staticmethod
    def _make_layout() -> QLayout:
        label = QLabel(
            "Please press the key combination you would like to assign.\n"
            "Supported modifiers: CTRL, ALT, SHIFT or META.\n"
            "Press ESC to delete the shortcut."
        )
        label.setAlignment(Qt.AlignCenter)
        layout = QVBoxLayout()
        layout.addWidget(label)
        return layout

    def _accept_value(self, value: Optional[str]) -> None:
        self._shortcut = value
        self.value_accepted.emit(value)  # type: ignore
        self.accept()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # https://stackoverflow.com/questions/35033116
        key, modifiers = int(event.key()), int(event.modifiers())

        if key == Qt.Key_Escape:
            self._accept_value(None)
        elif (
                modifiers
                and modifiers & self.MOD_MASK == modifiers
                and key > 0
                and key != Qt.Key_Shift
                and key != Qt.Key_Alt
                and key != Qt.Key_Control
                and key != Qt.Key_Meta
        ):
            self._accept_value(QKeySequence(modifiers + key).toString())

    def value(self) -> Optional[str]:
        return self._shortcut


class ShortCutGrabButton(QPushButton):
    _placeholder = '[Not assigned]'

    def __init__(self, initial_value: str = None):
        super().__init__(initial_value or self._placeholder)
        self._dialog = KeyPressDialog(self, initial_value)
        qconnect(self.clicked, self._dialog.exec)
        qconnect(self._dialog.value_accepted, lambda value: self.setText(value or self._placeholder))

    def value(self) -> str:
        return self._dialog.value() or ""


def detect_keypress():
    app = QApplication(sys.argv)
    w = QDialog()
    w.setWindowTitle("Test")
    w.setLayout(layout := QVBoxLayout())
    layout.addWidget(b := ShortCutGrabButton())  # type: ignore
    w.show()
    code = app.exec()
    print(f"{'Accepted' if w.result() else 'Rejected'}. Code: {code}, shortcut: \"{b.value()}\"")
    sys.exit(code)


if __name__ == '__main__':
    detect_keypress()
