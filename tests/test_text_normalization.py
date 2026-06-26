# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import pytest

from merge_notes.merge_notes import (
    cfg_strip,
    full_width_to_half_width,
    remove_furigana,
    strip_html,
    strip_punctuation,
)
from playground.no_anki_config import NoAnkiConfigView


@pytest.mark.parametrize(
    "text,expected",
    [
        ("<b>word</b>", "word"),
        (" plain ", "plain"),
    ],
)
def test_strip_html(text: str, expected: str) -> None:
    """HTML stripping removes tags and surrounding whitespace."""
    assert strip_html(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("漢字[かんじ]", "漢字"),
        ("abc def[reading]", "abcdef"),
    ],
)
def test_remove_furigana(text: str, expected: str) -> None:
    """Bracketed furigana is removed from text."""
    assert remove_furigana(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("１２３ＡＢＣ", "123ABC"),
        ("ｶﾀｶﾅ", "カタカナ"),
    ],
)
def test_full_width_to_half_width(text: str, expected: str) -> None:
    """Full-width text is normalized."""
    assert full_width_to_half_width(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("a,b.c", "abc"),
        ("no punctuation", "no punctuation"),
    ],
)
def test_strip_punctuation(no_anki_config: NoAnkiConfigView, text: str, expected: str) -> None:
    """Configured punctuation characters are removed from text."""
    no_anki_config["punctuation_characters"] = ",."
    assert strip_punctuation(text, no_anki_config) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("<b>漢字[かんじ]！１２３</b>", "漢字123"),
        ("  Hello！ ", "Hello"),
    ],
)
def test_cfg_strip_enabled_flags(no_anki_config: NoAnkiConfigView, text: str, expected: str) -> None:
    """Configured normalization options are applied together."""
    no_anki_config["ignore_furigana"] = True
    no_anki_config["punctuation_characters"] = "！"
    assert cfg_strip(text, no_anki_config) == expected


@pytest.mark.parametrize(
    "key,text,expected",
    [
        ("ignore_html_tags", "<b>x</b>", "<b>x</b>"),
        ("ignore_punctuation", "x！", "x!"),
        ("full-width_as_half-width", "１２", "１２"),
    ],
)
def test_cfg_strip_disabled_flags(no_anki_config: NoAnkiConfigView, key: str, text: str, expected: str) -> None:
    """Disabled normalization options leave matching content unchanged."""
    no_anki_config[key] = False
    no_anki_config["punctuation_characters"] = "！"
    assert cfg_strip(text, no_anki_config) == expected
