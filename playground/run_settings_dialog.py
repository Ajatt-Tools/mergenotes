# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import sys

from aqt.qt import QApplication

from merge_notes.settings_dialog import MergeFieldsSettingsWindow
from playground.no_anki_config import NoAnkiConfigView


def main() -> None:
    """Launch the Merge Notes settings dialog without a running Anki instance."""
    app = QApplication(sys.argv)
    cfg = NoAnkiConfigView()
    dialog = MergeFieldsSettingsWindow(cfg)
    dialog.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
