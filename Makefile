.PHONY: setup lint test deploy run-cli run-ui

setup:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

lint:
	python -m pyflakes src || true

test:
	pytest -q

deploy:
	./scripts/deploy.sh

run-cli:
	python -m scripts.chat_cli

run-ui:
	streamlit run apps/chat_ui_streamlit.py
