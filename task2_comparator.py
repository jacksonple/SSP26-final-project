from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

NO_NAME_DIFFERENCES = "NO DIFFERENCES IN REGARDS TO ELEMENT NAMES"
NO_REQUIREMENT_DIFFERENCES = "NO DIFFERENCES IN REGARDS TO ELEMENT REQUIREMENTS"


def load_yaml_files(file1: str, file2: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load and validate the two YAML files produced by Task 1."""

    return (_load_yaml_file(file1), _load_yaml_file(file2))


def compare_kde_names(
    yaml1: dict[str, Any],
    yaml2: dict[str, Any],
    file1_name: str,
    file2_name: str,
    output_file: str,
) -> str:
    """Compare only KDE names and write a deterministic text report."""

    names1 = set(_build_name_map(yaml1))
    names2 = set(_build_name_map(yaml2))

    rows: list[str] = []
    for name in sorted(names1 - names2):
        rows.append(f"{name},ABSENT-IN-{file2_name},PRESENT-IN-{file1_name}")
    for name in sorted(names2 - names1):
        rows.append(f"{name},ABSENT-IN-{file1_name},PRESENT-IN-{file2_name}")

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        if rows:
            handle.write("\n".join(rows) + "\n")
        else:
            handle.write(NO_NAME_DIFFERENCES + "\n")

    return str(output_path)


def compare_kde_requirements(
    yaml1: dict[str, Any],
    yaml2: dict[str, Any],
    file1_name: str,
    file2_name: str,
    output_file: str,
) -> str:
    """Compare KDE names and requirements using the README tuple format."""

    map1 = _build_name_map(yaml1)
    map2 = _build_name_map(yaml2)
    rows: list[str] = []

    for name in sorted(set(map1) | set(map2)):
        in_file1 = name in map1
        in_file2 = name in map2

        if in_file1 and not in_file2:
            rows.append(f"{name},ABSENT-IN-{file2_name},PRESENT-IN-{file1_name},NA")
            continue
        if in_file2 and not in_file1:
            rows.append(f"{name},ABSENT-IN-{file1_name},PRESENT-IN-{file2_name},NA")
            continue

        for requirement in sorted(map1[name] - map2[name]):
            rows.append(
                f"{name},ABSENT-IN-{file2_name},PRESENT-IN-{file1_name},{requirement}"
            )
        for requirement in sorted(map2[name] - map1[name]):
            rows.append(
                f"{name},ABSENT-IN-{file1_name},PRESENT-IN-{file2_name},{requirement}"
            )

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        if rows:
            handle.write("\n".join(rows) + "\n")
        else:
            handle.write(NO_REQUIREMENT_DIFFERENCES + "\n")

    return str(output_path)


def _load_yaml_file(file_path: str) -> dict[str, Any]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {file_path}")
    if path.suffix.lower() not in {".yaml", ".yml"}:
        raise ValueError(f"Expected a .yaml/.yml file: {file_path}")

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a dictionary: {file_path}")
    return data


def _build_name_map(yaml_data: dict[str, Any]) -> dict[str, set[str]]:
    name_map: dict[str, set[str]] = {}
    for key, value in yaml_data.items():
        if not isinstance(value, dict):
            continue
        name = str(value.get("name", key)).strip()
        requirements = {
            str(requirement).strip()
            for requirement in value.get("requirements", [])
            if str(requirement).strip()
        }
        if name:
            name_map[name] = requirements
    return name_map


__all__ = [
    "NO_NAME_DIFFERENCES",
    "NO_REQUIREMENT_DIFFERENCES",
    "load_yaml_files",
    "compare_kde_names",
    "compare_kde_requirements",
]
