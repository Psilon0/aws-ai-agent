.PHONY: setup lint test deploy

setup:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

lint:
	python -m pyflakes src || true

test:
	pytest -q

deploy:
	./scripts/deploy.sh
EOF
