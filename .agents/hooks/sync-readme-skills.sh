#!/bin/sh
# Claude adapter; shared updater itself has no harness dependency.
exec python3 "$(CDPATH= cd -- "$(dirname -- "$0")/../scripts" && pwd)/sync_skill_readme.py"
