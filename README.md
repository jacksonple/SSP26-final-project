# COMP 6700 Final Project

Final project for Secure Software Process at Auburn University.

## Team Members

- `Jack Plemons` - `jzp0162@auburn.edu`

## LLM

This project uses `google/gemma-3-1b-it` through Hugging Face Transformers for KDE extraction in Task 1.

## Project Overview

This repository compares two CIS benchmark PDFs, extracts key data elements (KDEs) with zero-shot, few-shot, and chain-of-thought prompting, computes KDE differences, maps those differences to Kubescape controls, and generates a final CSV report from Kubernetes security scans.

## Repository Structure

```text
.
├── .github/workflows/ci.yml      # GitHub Actions workflow
├── input_files/                  # CIS benchmark PDFs
│   ├── cis-r1.pdf
│   ├── cis-r2.pdf
│   ├── cis-r3.pdf
│   └── cis-r4.pdf
├── sample_output/                # Reference output for one example run
├── task_1.py                     # Extractor entrypoint
├── task_2.py                     # Comparator entrypoint
├── task_3.py                     # Kubescape executor entrypoint
├── pipeline.py                   # End-to-end pipeline for one PDF pair
├── run_all.py                    # Runs all 9 required input combinations
├── test_task_1.py                # Task 1 unit tests
├── test_task_2.py                # Task 2 unit tests
├── test_task_3.py                # Task 3 unit tests
├── test_pipeline.py              # End-to-end smoke test
├── PROMPT.md                     # Zero-shot, few-shot, and chain-of-thought prompts
├── requirements.txt              # Python dependencies
├── project-yamls.zip             # Kubernetes YAMLs for Kubescape scanning
├── run_project.sh                # Virtualenv-friendly TA runner
├── build_binary.sh               # PyInstaller build script
└── ssp_pipeline.spec             # Checked-in PyInstaller spec
```

Internal implementation files such as `main.py`, `task1_extractor.py`, `task2_comparator.py`, and `task3_executor.py` remain in the repository behind the public task entrypoints.

## Setup And Installation

### Prerequisites

- Python `3.12+`
- Kubescape installed and available on `PATH`
- A Hugging Face account with access to `google/gemma-3-1b-it`

### Virtual Environment Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Hugging Face Authentication

Authenticate before the first real Task 1 run if the model is not already cached locally:

```bash
huggingface-cli login
```

## Running The Project

### Option 1: Python For One Input Pair

```bash
python pipeline.py input_files/cis-r1.pdf input_files/cis-r2.pdf
```

### Option 2: Python For All 9 Required Input Combinations

```bash
python run_all.py
```

### Option 3: TA Runner Script

Run the full project inside a Python virtual environment:

```bash
./run_project.sh --run-all-default-pairs
```

Run a single pair:

```bash
./run_project.sh input_files/cis-r1.pdf input_files/cis-r2.pdf
```

### Required Input Pairs

| Input | Document 1 | Document 2 |
| --- | --- | --- |
| 1 | `cis-r1.pdf` | `cis-r1.pdf` |
| 2 | `cis-r1.pdf` | `cis-r2.pdf` |
| 3 | `cis-r1.pdf` | `cis-r3.pdf` |
| 4 | `cis-r1.pdf` | `cis-r4.pdf` |
| 5 | `cis-r2.pdf` | `cis-r2.pdf` |
| 6 | `cis-r2.pdf` | `cis-r3.pdf` |
| 7 | `cis-r2.pdf` | `cis-r4.pdf` |
| 8 | `cis-r3.pdf` | `cis-r3.pdf` |
| 9 | `cis-r3.pdf` | `cis-r4.pdf` |

## Output

The pipeline writes pair-specific artifacts under `outputs/`.

Example:

```text
outputs/
└── cis-r1_vs_cis-r2/
    ├── cis-r1-kdes.yaml
    ├── cis-r2-kdes.yaml
    ├── llm_output.txt
    ├── name_differences.txt
    ├── requirement_differences.txt
    ├── kubescape_controls.txt
    └── kubescape_results.csv
```

If the same PDF is used twice, Task 1 disambiguates the YAML filenames with `doc1-` and `doc2-` prefixes.

| File | Description | Task |
| --- | --- | --- |
| `*-kdes.yaml` | Extracted KDEs for each input PDF | Task 1 |
| `llm_output.txt` | Logged prompt/output records for all prompt styles | Task 1 |
| `name_differences.txt` | KDE name differences | Task 2 |
| `requirement_differences.txt` | KDE requirement differences in README/assignment tuple format | Task 2 |
| `kubescape_controls.txt` | Selected Kubescape controls or `NO DIFFERENCES FOUND` | Task 3 |
| `kubescape_results.csv` | Final scan output with the required columns | Task 3 |

An example reference run is committed under `sample_output/cis-r1_vs_cis-r2/`.

## Testing And CI

Run the full test suite locally:

```bash
python -m pytest -q
```

Run tests and then print `git status` locally:

```bash
./scripts/git_status_with_tests.sh
```

GitHub Actions also runs the test suite on:

- `push`
- `pull_request`
- `workflow_dispatch`

## Building The PyInstaller Binary

Build the binary with:

```bash
./build_binary.sh
```

The generated executable is written to:

```text
dist/ssp_pipeline
```

The binary packages the project code and Python dependencies, but Kubescape still needs to be installed on the system. On the first real run, the Gemma model may be downloaded from Hugging Face if it is not already cached.
