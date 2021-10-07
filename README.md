![Menu](https://user-images.githubusercontent.com/69171671/101429753-99032900-38fb-11eb-8b8d-06720ee7ef9a.png)

# mergenotes

[![Rate on AnkiWeb](https://glutanimate.com/logos/ankiweb-rate.svg)](https://ankiweb.net/shared/info/1425504015)
[![Patreon](https://img.shields.io/badge/patreon-support-orange)](https://www.patreon.com/bePatron?u=43555128)
[![Matrix](https://img.shields.io/badge/chat-join-green.svg)](https://tatsumoto-ren.github.io/blog/join-our-community.html)
![GitHub](https://img.shields.io/github/license/Ajatt-Tools/mergenotes)

Suppose you have a subs2srs deck.
Due to the way subs2srs works usually many sentences in the deck are split between multiple notes.
This addon adds a button to the Anki Browser that allows you to merge contents of selected cards.

## Features

1) Change settings before merging.
To open quick settings, click **Edit → Merge Fields Settings** in the Anki Browser.
2) Ability to specify `fields separator`.
You can decide what string is inserted as a separator between the merged fields.
3) Merge tags of selected cards.
4) Delete original notes after merging.
5) Choose direction of the merge: by `Due` number or `Sort Field`.
6) Merge in reverse order.
7) Skip non-empty fields to perform a partial merge.
8) Merge duplicate notes.
Go to "Browser" > "Notes" > "Find duplicates",
search duplicates and click "Merge duplicates" after the search has finished.

![screenshot](https://user-images.githubusercontent.com/69171671/136308551-69415b22-bed3-41e6-8bb9-6668ea66907f.png)

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
and selecting "Edit" > "Merge Fields Settings...".
Before merging duplicates, I recommend enabling the "Delete original notes" option.

## Demo

![screenshot](https://user-images.githubusercontent.com/69171671/101195632-9d0f1c80-3657-11eb-986b-97ffc11a280c.png)
