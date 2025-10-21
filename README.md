# FinSense – AWS AI Agent (Hackathon)

**One-line pitch:** An autonomous financial copilot that simulates portfolio outcomes and returns concise, actionable advice. *(Educational only; not financial advice.)*

## Quick Start (Local)
```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install streamlit plotly
PYTHONPATH=$(pwd) streamlit run apps/chat_ui_streamlit.py
