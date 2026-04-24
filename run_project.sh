#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${VENV_DIR:-${ROOT_DIR}/.venv}"
PYTHON_BIN="${PYTHON_BIN:-python3.12}"
export PIP_DISABLE_PIP_VERSION_CHECK=1

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  PYTHON_BIN="python3"
fi

"${PYTHON_BIN}" -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r "${ROOT_DIR}/requirements.txt"

if [ "$#" -eq 0 ]; then
  python "${ROOT_DIR}/run_all.py" --output-dir "${ROOT_DIR}/outputs"
else
  python "${ROOT_DIR}/pipeline.py" "$@"
fi
