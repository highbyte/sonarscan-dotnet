#!/usr/bin/env bash
set -eo pipefail
set +x
sample_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$sample_dir/verify-image.py" "$@"
