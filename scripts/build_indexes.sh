#!/bin/bash
set -e
export KMP_DUPLICATE_LIB_OK=TRUE
./.venv/bin/python3 -m app.ingestion.indexer
