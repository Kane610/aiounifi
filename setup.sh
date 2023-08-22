#!/usr/bin/env bash
# Setup the repository.

# Stop on errors
set -e

cd "$(dirname "$0")"

python3 -m venv venv
source venv/bin/activate

python3 -m pip install .[requirements] .[requirements_test] .[requirements_dev]
