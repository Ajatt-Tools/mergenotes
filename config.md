## Merge Notes configuration

**Anki needs to be restarted after changing the config.**

* `shortcut` - A key combination used to perform a merge.
* `delete_original_notes` - Delete redundant notes after merging.
* `merge_tags` - Merge tags of selected notes in addition to contents of fields.
* `field_separator` - This string is inserted between the merged fields.
Empty by default. Common options would be to change it to a single space: `" "`,
or to a linebreak: `"<br>"`.
* `ordering` - The way cards are sorted before merging.
Currently there are two options: `Due` and `Sort Field`.
* `reverse_order` - Sort cards in reverse.
For `Due` ordering this would mean that a card with the biggest due number
will receive the content of other selected cards.
* `show_duplicate_notes_button` - Add a duplicate button to the browser context menu.
* `dup_note_shortcut` - A key combination for the "duplicate notes" action.
