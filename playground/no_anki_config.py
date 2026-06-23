# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import copy
import json
import pathlib

from merge_notes.config import MergeNotesConfig


class NoAnkiConfigView(MergeNotesConfig):
    """Load Merge Notes config defaults without a running Anki instance."""

    config_json_path = pathlib.Path(__file__).parent.parent / "merge_notes" / "config.json"

    def _set_underlying_dicts(self) -> None:
        """Load config dictionaries from config.json."""
        with open(self.config_json_path, encoding="utf-8") as config_file:
            self._default_config = json.load(config_file)
        self._config = copy.deepcopy(self._default_config)

    def write_config(self) -> None:
        """Ignore writes during tests."""
        print("write requested. doing nothing. config contents:")
        print(json.dumps(self._config, indent=4, ensure_ascii=False))
