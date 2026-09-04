#!/bin/sh

cd "$(dirname "$(realpath "$0")")" || exit
uv run python-arch-wiki "$@"

