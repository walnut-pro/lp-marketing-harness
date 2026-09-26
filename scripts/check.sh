#!/usr/bin/env bash
# 知識データの整合性チェック（コミット前に実行）
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/validate_catalog.py
python3 scripts/build_context.py --check
echo "OK: catalog is valid and knowledge/context is up to date"
