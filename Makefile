.PHONY: clean dev smoke build deploy

clean:
	find . -name "__pycache__" -type d -prune -exec rm -rf {} + || true
	rm -rf .aws-sam || true
	rm -rf runs/outputs || true

dev:
	PYTHONPATH=$$(pwd) python -m streamlit run apps/chat_ui_streamlit.py

smoke:
	python - <<'PY'
from src.pipeline import run_pipeline
print(run_pipeline({'risk_profile':'moderate','horizon_years':5,'age':30,'context':{'demo_seed':123}}))
PY

build:
	sam build

deploy:
	sam deploy --guided
