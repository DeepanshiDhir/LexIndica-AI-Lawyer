#!/bin/bash
set -e
export KMP_DUPLICATE_LIB_OK=TRUE
export PYTHONPATH=.
./.venv/bin/streamlit run app/frontend/streamlit_app.py --server.port 8501
