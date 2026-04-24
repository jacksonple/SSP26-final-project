#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${VENV_DIR:-${ROOT_DIR}/.venv}"
PYTHON_BIN="${PYTHON_BIN:-python3.12}"
export PIP_DISABLE_PIP_VERSION_CHECK=1
export KMP_USE_SHM=0
export TOKENIZERS_PARALLELISM=false
export PYTORCH_ENABLE_MPS_FALLBACK=1

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  PYTHON_BIN="python3"
fi

"${PYTHON_BIN}" -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r "${ROOT_DIR}/requirements.txt"

PYI_BUILD_MODE=onedir pyinstaller --clean --noconfirm "${ROOT_DIR}/ssp_pipeline.spec"
"${ROOT_DIR}/dist/ssp_pipeline/ssp_pipeline" --help >/dev/null

PYI_BUILD_MODE=onefile pyinstaller --clean --noconfirm "${ROOT_DIR}/ssp_pipeline.spec"
"${ROOT_DIR}/dist/ssp_pipeline" --help >/dev/null
