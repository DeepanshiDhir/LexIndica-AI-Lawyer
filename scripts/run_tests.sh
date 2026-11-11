#!/bin/bash
set -e
export KMP_DUPLICATE_LIB_OK=TRUE
export LEGAL_AI_OFFLINE=1
./.venv/bin/pytest tests/ -v
