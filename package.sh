#!/usr/bin/env sh

readonly ADDON_NAME=mergenotes
readonly ROOT_DIR=$(git rev-parse --show-toplevel)
readonly BRANCH=${1:-$(git branch --show-current)}
readonly ZIP_NAME=${ADDON_NAME}_${BRANCH}.ankiaddon

cd -- "$ROOT_DIR" || exit 1

git archive "$BRANCH" --format=zip --output "$ZIP_NAME"
