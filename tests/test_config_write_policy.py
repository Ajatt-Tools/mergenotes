# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from collections.abc import Sequence
from unittest.mock import create_autospec

import pytest

from merge_notes.ajt_common import addon_config
from merge_notes.ajt_common.addon_config import AddonConfigManagerError, NumericValue
from merge_notes.config import MergeNotesConfig
from playground.no_anki_config import NoAnkiConfigView


@pytest.mark.usefixtures("config_backend")
class TestConfigWritePolicy:
    """Exercise the shared write policy through the add-on's actual configuration subclass."""

    @pytest.mark.parametrize("default", [False, True])
    def test_clone(self, monkeypatch: pytest.MonkeyPatch, default: bool) -> None:
        """Construct the actual subclass through clone and prevent either clone mode from writing."""
        clone = MergeNotesConfig.clone(default=default)
        assert isinstance(clone, MergeNotesConfig)
        assert clone.is_default is default
        write = create_autospec(addon_config.write_config)
        monkeypatch.setattr(addon_config, "write_config", write)
        with pytest.raises(AddonConfigManagerError):
            clone.write_config()
        write.assert_not_called()

    @pytest.mark.parametrize("allow_disk_writes", [False, True])
    def test_constructor_write_policy(self, monkeypatch: pytest.MonkeyPatch, allow_disk_writes: bool) -> None:
        """Forward constructor write protection without changing the normal writable default."""
        config = MergeNotesConfig(allow_disk_writes=allow_disk_writes)
        write = create_autospec(addon_config.write_config)
        monkeypatch.setattr(addon_config, "write_config", write)
        if allow_disk_writes:
            config.write_config()
            write.assert_called_once_with(config.config)
        else:
            with pytest.raises(AddonConfigManagerError, match="Writing to disk disabled"):
                config.write_config()
            write.assert_not_called()

    @pytest.mark.parametrize(
        "defaults,overrides,expected",
        [
            (
                {"count": 0, "ratio": 1.5, "enabled": True, "label": "text"},
                {"count": 3},
                [
                    NumericValue(value=3, cfg_key="count", default=0),
                    NumericValue(value=1.5, cfg_key="ratio", default=1.5),
                ],
            ),
            ({"enabled": False, "labels": []}, {}, []),
            ({}, {}, []),
        ],
    )
    def test_numerics(
        self,
        no_anki_config: NoAnkiConfigView,
        defaults: dict[str, object],
        overrides: dict[str, object],
        expected: Sequence[NumericValue],
    ) -> None:
        """Enumerate numeric defaults with current values, excluding booleans and nonnumeric settings."""
        no_anki_config.default_config.clear()
        no_anki_config.default_config.update(defaults)
        no_anki_config.config.clear()
        no_anki_config.config.update(overrides)
        assert list(MergeNotesConfig().numerics()) == expected
