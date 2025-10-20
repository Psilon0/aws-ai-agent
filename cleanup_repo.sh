#!/usr/bin/env bash
set -euo pipefail

echo ">>> Creating a backup branch 'pre-cleanup-$(date +%Y%m%d-%H%M%S)'"
git checkout -b "pre-cleanup-$(date +%Y%m%d-%H%M%S)" || true

echo ">>> Writing .gitignore"
cat > .gitignore <<'EOF'
# OS / Editor
.DS_Store
Thumbs.db
*.swp
*.swo
*.tmp
*.bak
*~

# Archives
*.zip
*.tar
*.tgz
*.gz
*.bz2
*.7z

# Logs
*.log

# Backup/merge leftovers
*.orig
*.old

# IDEs
.idea/
.vscode/*
!.vscode/extensions.json
!.vscode/settings.json

# Python
__pycache__/
*.py[cod]
*.pyd
.env
.venv/
venv/
.env.*
*.egg-info/
dist/
build/
.pytest_cache/
.mypy_cache/
.tox/
.coverage*
.ruff_cache/

# Extra patterns detected in your repo
.env
__pycache__/
EOF

echo ">>> Stage .gitignore"
git add .gitignore

echo ">>> Remove cached files that should be ignored (keeps them on disk)"
git rm -r --cached --ignore-unmatch __pycache__/ .ipynb_checkpoints/ node_modules/ dist/ build/ .venv venv .pytest_cache/ .mypy_cache/ .tox/ .parcel-cache/ .gradle/ target/ out/ .next .ruff_cache/ "*.pyc" "*.pyo" "*.pyd" "*.log" "*.orig" "*.old" "*~" "*.bak" 2>/dev/null || true

echo ">>> (Optional) Delete generated caches from disk (SAFE MODE: listing only)"
echo "Run the following to actually delete from disk:"
echo 'find . -type d -name "__pycache__" -prune -exec rm -rf {} +'
echo 'find . -type d -name ".ipynb_checkpoints" -prune -exec rm -rf {} +'
echo 'find . -type d -name "node_modules" -prune -exec rm -rf {} +'
echo 'find . -type f -name "*.pyc" -delete'
echo 'find . -type f -name "*.log" -delete'
echo 'find . -type f -name "*.bak" -delete'

echo ">>> Commit the cleanup"
git commit -m "Repo hygiene: add .gitignore and remove cached artifacts"

echo ">>> Done. Review 'git status' and 'git diff' before pushing."
