![Menu](https://user-images.githubusercontent.com/69171671/101429753-99032900-38fb-11eb-8b8d-06720ee7ef9a.png)

# Merge Notes

[![Rate on AnkiWeb](https://glutanimate.com/logos/ankiweb-rate.svg)](https://ankiweb.net/shared/info/1425504015)
[![Patreon](https://img.shields.io/badge/patreon-support-orange)](https://www.patreon.com/bePatron?u=43555128)
[![Matrix](https://img.shields.io/badge/chat-join-green.svg)](https://tatsumoto-ren.github.io/blog/join-our-community.html)
![GitHub](https://img.shields.io/github/license/Ajatt-Tools/mergenotes)

Suppose you have a subs2srs deck.
Due to the way subs2srs works usually many sentences in the deck are split between multiple notes.
This addon adds a button to the Anki Browser that allows you to merge contents of selected cards.

I recommend converting all notes to one `note type` before merging them.
The add-on will ignore the fields that are present in one note but are not present in the other.

## Features

1) **Merge** or **duplicate** selected notes.
2) Change settings before merging.
   To open quick settings, click "Edit" > "Merge Notes Settings" in the Anki Browser.
3) Ability to specify a field separator.
   You can decide what string is inserted as a separator between the merged fields.
4) Merge tags of selected cards.
5) Delete original notes after merging.
6) Choose direction of the merge: by `Due` number, by `Sort Field` or by `Sort Field (numeric)`.
   The latter checks if there's a number in the field and sorts by the number first.
7) Merge in reverse order.
8) Skip non-empty fields to perform a partial merge.
9) Merge duplicate notes.
   Go to "Browser" > "Notes" > "Find duplicates",
   search duplicates and click "Merge duplicates" after the search has finished.

## Installation

The addon can be installed from [Ankiweb](https://ankiweb.net/shared/info/1425504015), or manually:
```
git clone 'https://github.com/Ajatt-Tools/mergenotes.git' ~/.local/share/Anki2/addons21/mergenotes
```

## Configuration

To configure the add-on, open the Anki Add-on Menu
via "Tools" > "Add-ons" and select "mergenotes".
Then click the "Config" button on the right-side of the screen.

Most of the settings can be accessed by opening the Anki Browser
and selecting "Edit" > "Merge Notes Options...".
Before merging duplicates, I recommend enabling the "Delete original notes" option.

Field separator is the string inserted between the merged fields.
It is empty by default, but you can change it to a space, comma or any HTML tag like `<br>`.
You can also use escaped characters like "\n" or "\t" to insert a linebreak or tab.

## Screenshots

Merge notes

![screenshot](https://user-images.githubusercontent.com/69171671/136309709-32089f42-4fcc-4214-8e14-525fdaddd9cb.png)

Merge duplicates

![screenshot](https://user-images.githubusercontent.com/69171671/136308551-69415b22-bed3-41e6-8bb9-6668ea66907f.png)
