# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from typing import Optional

from aqt.qt import *


class KeyPressDialog(QDialog):
    MOD_MASK = Qt.CTRL | Qt.ALT | Qt.SHIFT | Qt.META

    def __init__(self, parent: QWidget = None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self._shortcut = None
        self.setMinimumSize(380, 64)
        self.setWindowTitle("Grab key combination")
        self.label = QLabel(
            "Please press the key combination you would like to assign.\n"
            "Supported modifiers: CTRL, ALT, SHIFT or META.\n"
            "Press ESC to delete the shortcut."
        )
        self.setLayout(self._make_layout())

    def _make_layout(self) -> QLayout:
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.label.setAlignment(Qt.AlignCenter)
        return layout

    def value(self) -> Optional[str]:
        return self._shortcut

    def keyPressEvent(self, event) -> None:
        # https://stackoverflow.com/questions/35033116
        key, modifiers = int(event.key()), int(event.modifiers())

        if key == Qt.Key_Escape:
            self._shortcut = None
            self.accept()
        elif (
                modifiers
                and modifiers & self.MOD_MASK == modifiers
                and key > 0
                and key != Qt.Key_Shift
                and key != Qt.Key_Alt
                and key != Qt.Key_Control
                and key != Qt.Key_Meta
        ):
            self._shortcut = QKeySequence(modifiers + key).toString()
            self.accept()


class ShortCutGrabButton(QPushButton):
    _placeholder = '[Not assigned]'

    def __init__(self, initial_value: str = None):
        super().__init__(initial_value or self._placeholder)
        self._value = initial_value
        self.clicked.connect(self._on_change_shortcut)

    def value(self) -> str:
        return self._value or ''

    def _on_change_shortcut(self):
        if (d := KeyPressDialog(self)).exec():
            self._value = d.value()
            self.setText(self._value or self._placeholder)


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
