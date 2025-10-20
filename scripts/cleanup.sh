#!/usr/bin/env bash
set -euo pipefail
echo "🧹 Removing caches and compiled files…"
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type f -name ".DS_Store" -delete
echo "Done."
