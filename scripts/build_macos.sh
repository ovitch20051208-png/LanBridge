#!/bin/sh
set -eu
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
python3 "$script_dir/build.py" --dmg
python3 "$script_dir/smoke_bundle.py" "$script_dir/../dist/LanBridge.app/Contents/MacOS/LanBridge"
