#!/bin/bash

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$DIR/../.." && pwd)"
PYTHONPATH="$REPO_ROOT/python-algo${PYTHONPATH:+:$PYTHONPATH}" \
  exec "${PYTHON_CMD:-python3}" -u "$DIR/algo_strategy.py"
