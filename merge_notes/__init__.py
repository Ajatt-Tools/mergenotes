# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import sys

from aqt import mw


def start_addon() -> None:
    from . import (
        duplicate_notes,
        find_duplicates,
        merge_duplicates,
        merge_notes,
        settings_dialog,
    )

    merge_notes.init()
    merge_duplicates.init()
    settings_dialog.init()
    duplicate_notes.init()
    find_duplicates.init()


if mw and "pytest" not in sys.modules:
    start_addon()
