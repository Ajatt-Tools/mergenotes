#!/bin/bash

set -euo pipefail

readonly ROOT_DIR=$(git rev-parse --show-toplevel)

"$ROOT_DIR/merge_notes/ajt_common/format.sh" \
	--exclude merge_notes/ajt_common
