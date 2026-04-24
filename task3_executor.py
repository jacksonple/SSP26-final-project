from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd

KDE_CONTROL_MAP = {
    "access": ["C-0002", "C-0035", "C-0065"],
    "auth": ["C-0002", "C-0005", "C-0020"],
    "authoriz": ["C-0035", "C-0065"],
    "encrypt": ["C-0007", "C-0066"],
    "network": ["C-0021", "C-0030", "C-0041", "C-0044"],
    "log": ["C-0031", "C-0067"],
    "audit": ["C-0031", "C-0067"],
    "secret": ["C-0012", "C-0020"],
    "privilege": ["C-0013", "C-0016", "C-0046", "C-0057"],
    "container": ["C-0001", "C-0006", "C-0013", "C-0017"],
    "rbac": ["C-0035", "C-0065"],
    "pod": ["C-0014", "C-0015", "C-0038", "C-0061"],
    "resource": ["C-0004", "C-0009"],
    "image": ["C-0001", "C-0078"],
    "namespace": ["C-0061"],
    "storage": ["C-0006", "C-0045", "C-0048"],
    "service account": ["C-0034", "C-0053"],
    "credential": ["C-0012", "C-0020"],
    "tls": ["C-0007"],
    "certificat": ["C-0007"],
    "password": ["C-0012"],
    "patch": ["C-0078"],
    "vulnerab": ["C-0078"],
    "compliance": ["C-0009"],
    "firewall": ["C-0021", "C-0030"],
    "monitor": ["C-0067"],
    "baseline": ["C-0009", "C-0055"],
    "configuration": ["C-0012", "C-0017"],
    "user": ["C-0002", "C-0035"],
    "account": ["C-0002", "C-0034"],
}

DEFAULT_CONTROLS = [
    "C-0002",
    "C-0004",
    "C-0005",
    "C-0007",
    "C-0009",
    "C-0012",
    "C-0013",
    "C-0016",
    "C-0021",
    "C-0030",
    "C-0031",
    "C-0035",
    "C-0046",
    "C-0057",
    "C-0065",
    "C-0066",
    "C-0067",
]

NO_DIFF_MARKER = "NO DIFFERENCES FOUND"
TASK2_NO_DIFF_MARKERS = {
    "NO DIFFERENCES IN REGARDS TO ELEMENT NAMES",
    "NO DIFFERENCES IN REGARDS TO ELEMENT REQUIREMENTS",
    NO_DIFF_MARKER,
}
CSV_COLUMNS = [
    "FilePath",
    "Severity",
    "Control name",
    "Failed resources",
    "All Resources",
    "Compliance score",
]


def load_text_files(file1: str, file2: str) -> tuple[str, str]:
    """Load the two comparator text outputs."""

    return (_load_text_file(file1), _load_text_file(file2))


def map_differences_to_controls(text1: str, text2: str, output_file: str) -> list[str]:
    """Map comparator output to Kubescape control IDs and write the control file."""

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if _is_no_difference_text(text1) and _is_no_difference_text(text2):
        output_path.write_text(NO_DIFF_MARKER + "\n", encoding="utf-8")
        return [NO_DIFF_MARKER]

    combined_text = f"{text1}\n{text2}".lower()
    controls: set[str] = set()
    for keyword, control_ids in KDE_CONTROL_MAP.items():
        if keyword in combined_text:
            controls.update(control_ids)

    selected_controls = sorted(controls) if controls else DEFAULT_CONTROLS
    output_path.write_text("\n".join(selected_controls) + "\n", encoding="utf-8")
    return selected_controls


def execute_kubescape(controls: list[str], yaml_zip: str) -> pd.DataFrame:
    """Run Kubescape on the project YAML bundle and return normalized results."""

    zip_path = Path(yaml_zip)
    if not zip_path.exists():
        raise FileNotFoundError(f"YAML zip not found: {yaml_zip}")

    if not _kubescape_available():
        _install_kubescape()
    if not _kubescape_available():
        raise RuntimeError("kubescape is not installed and could not be installed automatically.")

    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(zip_path, "r") as archive:
            archive.extractall(temp_dir)

        if controls == [NO_DIFF_MARKER]:
            command = ["kubescape", "scan", temp_dir, "--format", "json"]
        else:
            control_arg = ",".join(controls)
            command = ["kubescape", "scan", "control", control_arg, temp_dir, "--format", "json"]

        result = subprocess.run(command, capture_output=True, text=True, timeout=300)
        if result.returncode not in (0, 1):
            raise RuntimeError(
                f"kubescape exited with code {result.returncode}: {result.stderr[:400]}"
            )

        return _parse_kubescape_output(result.stdout)


def generate_csv(df: pd.DataFrame, output_file: str) -> str:
    """Write the normalized Kubescape dataframe to CSV with the required columns."""

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    normalized_df = df.copy()
    for column in CSV_COLUMNS:
        if column not in normalized_df.columns:
            normalized_df[column] = "N/A"

    normalized_df[CSV_COLUMNS].to_csv(output_path, index=False)
    return str(output_path)


def _load_text_file(file_path: str) -> str:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Text file not found: {file_path}")
    return path.read_text(encoding="utf-8")


def _is_no_difference_text(text: str) -> bool:
    stripped = text.strip()
    return stripped in TASK2_NO_DIFF_MARKERS


def _kubescape_available() -> bool:
    return shutil.which("kubescape") is not None


def _install_kubescape() -> bool:
    install_command = (
        "curl -s https://raw.githubusercontent.com/kubescape/kubescape/master/install.sh | /bin/bash"
    )
    result = subprocess.run(
        install_command,
        shell=True,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _parse_kubescape_output(raw_output: str) -> pd.DataFrame:
    data = _load_json_payload(raw_output)
    if not isinstance(data, dict):
        return _empty_df()

    rows: list[dict[str, Any]] = []

    for framework in data.get("results", []):
        source_label = framework.get("name", "unknown")
        for control in framework.get("controls", []):
            rows.append(_control_to_row(control, source_label))

    if not rows:
        summary_controls = data.get("summaryDetails", {}).get("controls", {})
        if isinstance(summary_controls, dict):
            for control_id, control in summary_controls.items():
                rows.append(_control_to_row(control, control_id))

    if not rows and isinstance(data.get("controls"), list):
        for control in data["controls"]:
            rows.append(_control_to_row(control, "kubescape"))

    return pd.DataFrame(rows, columns=CSV_COLUMNS) if rows else _empty_df()


def _load_json_payload(raw_output: str) -> Any:
    try:
        return json.loads(raw_output)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", raw_output)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None


def _control_to_row(control: dict[str, Any], source_label: str) -> dict[str, Any]:
    severity_value = control.get("severity", {})
    if isinstance(severity_value, dict):
        severity = (
            severity_value.get("name")
            or severity_value.get("scoreFactor")
            or severity_value.get("severity")
            or "Unknown"
        )
    elif isinstance(severity_value, (int, float)):
        severity = _score_to_label(float(severity_value))
    else:
        severity = str(severity_value or "Unknown")

    return {
        "FilePath": control.get("filePath") or control.get("path") or source_label,
        "Severity": severity,
        "Control name": control.get("name") or control.get("controlID") or "Unknown",
        "Failed resources": control.get("numberOfFailedResources", 0),
        "All Resources": control.get("numberOfAllResources", 0),
        "Compliance score": control.get("complianceScore", 0),
    }


def _score_to_label(score: float) -> str:
    if score >= 8:
        return "Critical"
    if score >= 6:
        return "High"
    if score >= 4:
        return "Medium"
    if score >= 2:
        return "Low"
    return "Unknown"


def _empty_df() -> pd.DataFrame:
    return pd.DataFrame(columns=CSV_COLUMNS)


__all__ = [
    "NO_DIFF_MARKER",
    "CSV_COLUMNS",
    "load_text_files",
    "map_differences_to_controls",
    "execute_kubescape",
    "generate_csv",
]
