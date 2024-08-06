# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from . import duplicate_notes, find_duplicates, merge_duplicates, merge_notes, settings_dialog

merge_notes.init()
merge_duplicates.init()
settings_dialog.init()
duplicate_notes.init()
find_duplicates.init()
