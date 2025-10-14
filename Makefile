.PHONY: setup lint test deploy

setup:
\tpython -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

lint:
\tpython -m pyflakes src || true

test:
\tpytest -q

deploy:
\t./scripts/deploy.sh
