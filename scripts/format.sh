#!/bin/bash

set -euo pipefail

readonly ROOT_DIR=$(git rev-parse --show-toplevel)

# Scope formatting here so every entry point includes the shared code and playground.
"$ROOT_DIR/merge_notes/ajt_common/format.sh" \
	--include merge_notes \
	--include tests \
	--include playground \
	"$@"
