# SSP Spring 2026 Final Project

## Team

- `Jack Plemons` — `jzp0162@auburn.edu`

## Task-1 LLM

- `google/gemma-3-1b-it`

## Project Summary

This project compares two security requirements PDFs, extracts key data elements (KDEs) with Gemma-3-1B using zero-shot, few-shot, and chain-of-thought prompts, computes YAML and requirement differences, maps those differences to Kubescape controls, and scans `project-yamls.zip` to generate a final CSV report.

## Repository Layout

- [.github/workflows/ci.yml](/Users/jackplemons/Downloads/continuous-secsoft/ssp-spr26/project/.github/workflows/ci.yml): GitHub Actions workflow
- [input_files](/Users/jackplemons/Downloads/continuous-secsoft/ssp-spr26/project/input_files): the four CIS benchmark PDFs used by the pipeline
- [sample_output](/Users/jackplemons/Downloads/continuous-secsoft/ssp-spr26/project/sample_output): reserved location for reference artifacts
- [task_1.py](/Users/jackplemons/Downloads/continuous-secsoft/ssp-spr26/project/task_1.py): Task 1 public entrypoint for PDF loading, prompt construction, Gemma extraction, and YAML generation
- [task_2.py](/Users/jackplemons/Downloads/continuous-secsoft/ssp-spr26/project/task_2.py): Task 2 public entrypoint for KDE name and requirement comparison
- [task_3.py](/Users/jackplemons/Downloads/continuous-secsoft/ssp-spr26/project/task_3.py): Task 3 public entrypoint for Kubescape control mapping, scan execution, and CSV generation
- [pipeline.py](/Users/jackplemons/Downloads/continuous-secsoft/ssp-spr26/project/pipeline.py): single-pair pipeline entrypoint
- [run_all.py](/Users/jackplemons/Downloads/continuous-secsoft/ssp-spr26/project/run_all.py): batch runner for the nine required PDF pairs
- [test_task_1.py](/Users/jackplemons/Downloads/continuous-secsoft/ssp-spr26/project/test_task_1.py), [test_task_2.py](/Users/jackplemons/Downloads/continuous-secsoft/ssp-spr26/project/test_task_2.py), and [test_task_3.py](/Users/jackplemons/Downloads/continuous-secsoft/ssp-spr26/project/test_task_3.py): unit tests for the three assignment tasks
- [test_pipeline.py](/Users/jackplemons/Downloads/continuous-secsoft/ssp-spr26/project/test_pipeline.py): end-to-end smoke test for the pipeline
- [PROMPT.md](/Users/jackplemons/Downloads/continuous-secsoft/ssp-spr26/project/PROMPT.md): the three prompt templates used by Task 1
- [requirements.txt](/Users/jackplemons/Downloads/continuous-secsoft/ssp-spr26/project/requirements.txt): pinned Python dependencies

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Python 3.12 is the recommended local runtime for this project. Python 3.13 may require additional native build tooling for `sentencepiece`.

## Run The Pipeline

Run one PDF pair:

```bash
python pipeline.py input_files/cis-r1.pdf input_files/cis-r2.pdf
```

Run all nine assignment pairs:

```bash
python run_all.py
```

Write outputs to a different root directory:

```bash
python pipeline.py input_files/cis-r1.pdf input_files/cis-r2.pdf --output-dir custom_outputs
```

Use a non-default YAML archive:

```bash
python pipeline.py input_files/cis-r1.pdf input_files/cis-r2.pdf --project-yamls-zip /path/to/project-yamls.zip
```

## Output Layout

Each run creates one pair-specific directory under `outputs/`:

```text
outputs/
  cis-r1_vs_cis-r2/
    cis-r1-kdes.yaml
    cis-r2-kdes.yaml
    llm_output.txt
    name_differences.txt
    requirement_differences.txt
    kubescape_controls.txt
    kubescape_results.csv
```

If the same PDF is used twice, the KDE files are disambiguated as `doc1-<name>-kdes.yaml` and `doc2-<name>-kdes.yaml`.

## Testing

Run all tests:

```bash
python -m pytest -q
```

## GitHub Actions And The `git status` Requirement

GitHub Actions cannot be triggered by a local `git status` command. To satisfy the grading intent, this repository includes:

- a GitHub Actions workflow at [ci.yml](/Users/jackplemons/Downloads/continuous-secsoft/ssp-spr26/project/.github/workflows/ci.yml) that runs on `push`, `pull_request`, and `workflow_dispatch`
- a local helper script at [git_status_with_tests.sh](/Users/jackplemons/Downloads/continuous-secsoft/ssp-spr26/project/scripts/git_status_with_tests.sh) that runs the full pytest suite and then runs `git status`

## TA Quick Start

Run everything inside a fresh virtual environment:

```bash
./run_project.sh --run-all-default-pairs
```

Run a single pair:

```bash
./run_project.sh input_files/cis-r1.pdf input_files/cis-r2.pdf
```

## Build The PyInstaller Binary

```bash
./build_binary.sh
```

The binary will be created in `dist/ssp_pipeline`.
