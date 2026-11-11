#!/bin/bash
set -e
export KMP_DUPLICATE_LIB_OK=TRUE
export PYTHONPATH=.
./.venv/bin/python3 app/main.py cli
