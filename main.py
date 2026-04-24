from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import task1_extractor
import task2_comparator
import task3_executor

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT_DIR = PROJECT_ROOT / "input_files"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "outputs"
DEFAULT_YAML_ZIP = PROJECT_ROOT / "project-yamls.zip"
DEFAULT_PDF_PAIRS = [
    ("cis-r1.pdf", "cis-r1.pdf"),
    ("cis-r1.pdf", "cis-r2.pdf"),
    ("cis-r1.pdf", "cis-r3.pdf"),
    ("cis-r1.pdf", "cis-r4.pdf"),
    ("cis-r2.pdf", "cis-r2.pdf"),
    ("cis-r2.pdf", "cis-r3.pdf"),
    ("cis-r2.pdf", "cis-r4.pdf"),
    ("cis-r3.pdf", "cis-r3.pdf"),
    ("cis-r3.pdf", "cis-r4.pdf"),
]


def run_pipeline_for_pair(
    pdf1: str,
    pdf2: str,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    project_yamls_zip: str | Path = DEFAULT_YAML_ZIP,
    llm_pipe: Any | None = None,
) -> dict[str, str]:
    """Run Tasks 1-3 for a single PDF pair and return artifact paths."""

    output_root_path = Path(output_root)
    pair_output_dir = output_root_path / _pair_label(pdf1, pdf2)
    pair_output_dir.mkdir(parents=True, exist_ok=True)

    document1, document2 = task1_extractor.load_documents(pdf1, pdf2)
    extraction_result = task1_extractor.extract_kdes_for_documents(
        document1=document1,
        document2=document2,
        output_dir=str(pair_output_dir),
        llm_pipe=llm_pipe,
    )

    yaml_path_1, yaml_path_2 = extraction_result["yaml_paths"]
    yaml_data_1, yaml_data_2 = task2_comparator.load_yaml_files(yaml_path_1, yaml_path_2)

    name_diff_path = task2_comparator.compare_kde_names(
        yaml1=yaml_data_1,
        yaml2=yaml_data_2,
        file1_name=Path(yaml_path_1).name,
        file2_name=Path(yaml_path_2).name,
        output_file=str(pair_output_dir / "name_differences.txt"),
    )
    requirement_diff_path = task2_comparator.compare_kde_requirements(
        yaml1=yaml_data_1,
        yaml2=yaml_data_2,
        file1_name=Path(yaml_path_1).name,
        file2_name=Path(yaml_path_2).name,
        output_file=str(pair_output_dir / "requirement_differences.txt"),
    )

    name_text, requirement_text = task3_executor.load_text_files(
        name_diff_path,
        requirement_diff_path,
    )
    controls = task3_executor.map_differences_to_controls(
        name_text,
        requirement_text,
        str(pair_output_dir / "kubescape_controls.txt"),
    )
    kubescape_df = task3_executor.execute_kubescape(
        controls,
        str(Path(project_yamls_zip)),
    )
    csv_path = task3_executor.generate_csv(
        kubescape_df,
        str(pair_output_dir / "kubescape_results.csv"),
    )

    return {
        "output_dir": str(pair_output_dir),
        "llm_output_file": extraction_result["llm_output_file"],
        "yaml_1": yaml_path_1,
        "yaml_2": yaml_path_2,
        "name_differences": name_diff_path,
        "requirement_differences": requirement_diff_path,
        "controls_file": str(pair_output_dir / "kubescape_controls.txt"),
        "csv_file": csv_path,
    }


def run_default_pairs(
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    project_yamls_zip: str | Path = DEFAULT_YAML_ZIP,
    llm_pipe: Any | None = None,
) -> list[dict[str, str]]:
    """Run the assignment's nine required PDF combinations."""

    shared_pipe = llm_pipe or task1_extractor._build_llm_pipeline()
    results: list[dict[str, str]] = []

    for pdf1_name, pdf2_name in DEFAULT_PDF_PAIRS:
        pdf1_path = DEFAULT_INPUT_DIR / pdf1_name
        pdf2_path = DEFAULT_INPUT_DIR / pdf2_name
        results.append(
            run_pipeline_for_pair(
                pdf1=str(pdf1_path),
                pdf2=str(pdf2_path),
                output_root=output_root,
                project_yamls_zip=project_yamls_zip,
                llm_pipe=shared_pipe,
            )
        )

    return results


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the SSP class project pipeline for one pair of PDFs or all default pairs."
    )
    parser.add_argument("pdf1", nargs="?", help="Path to the first PDF input.")
    parser.add_argument("pdf2", nargs="?", help="Path to the second PDF input.")
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="Directory where pair-specific artifact folders will be written.",
    )
    parser.add_argument(
        "--project-yamls-zip",
        default=str(DEFAULT_YAML_ZIP),
        help="Path to the project-yamls.zip bundle used by Kubescape.",
    )
    parser.add_argument(
        "--run-all-default-pairs",
        action="store_true",
        help="Run the nine PDF pairs required by the assignment.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    if args.run_all_default_pairs:
        results = run_default_pairs(
            output_root=args.output_dir,
            project_yamls_zip=args.project_yamls_zip,
        )
        for result in results:
            print(f"Completed {result['output_dir']}")
        return 0

    if not args.pdf1 or not args.pdf2:
        parser.error("pdf1 and pdf2 are required unless --run-all-default-pairs is used.")

    result = run_pipeline_for_pair(
        pdf1=args.pdf1,
        pdf2=args.pdf2,
        output_root=args.output_dir,
        project_yamls_zip=args.project_yamls_zip,
    )
    print(f"Artifacts written to {result['output_dir']}")
    return 0


def _pair_label(pdf1: str, pdf2: str) -> str:
    return f"{Path(pdf1).stem}_vs_{Path(pdf2).stem}"


if __name__ == "__main__":
    raise SystemExit(main())
