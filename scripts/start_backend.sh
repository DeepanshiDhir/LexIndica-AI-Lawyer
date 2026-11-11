#!/bin/bash
set -e
export KMP_DUPLICATE_LIB_OK=TRUE
export PYTHONPATH=.
./.venv/bin/uvicorn app.api.server:app --host 0.0.0.0 --port 8000
