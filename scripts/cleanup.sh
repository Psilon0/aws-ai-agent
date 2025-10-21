#!/usr/bin/env bash
set -euo pipefail
find . -name "__pycache__" -type d -prune -exec rm -rf {} + || true
rm -rf .aws-sam || true
