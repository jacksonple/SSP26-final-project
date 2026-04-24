from __future__ import annotations

from pathlib import Path

from pipeline import PROJECT_ROOT, run_pipeline_for_pair


if __name__ == "__main__":
    result = run_pipeline_for_pair(
        pdf1=str(PROJECT_ROOT / "input_files" / "cis-r1.pdf"),
        pdf2=str(PROJECT_ROOT / "input_files" / "cis-r2.pdf"),
        output_root=Path(PROJECT_ROOT / "demo_output"),
    )
    print(f"Demo artifacts written to {result['output_dir']}")
