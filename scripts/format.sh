#!/bin/bash

set -euo pipefail

readonly ROOT_DIR=$(git rev-parse --show-toplevel)

# Include shared code and playground scripts, but leave Hatch's generated version file alone.
"$ROOT_DIR/merge_notes/ajt_common/format.sh" \
	--include merge_notes \
	--include tests \
	--include playground \
	--exclude merge_notes/__about__.py \
	"$@"
