from __future__ import annotations

from pathlib import Path

import yaml

import task_2 as task2_comparator


def test_load_yaml_files_reads_two_yaml_documents(tmp_path):
    file1 = tmp_path / "one.yaml"
    file2 = tmp_path / "two.yaml"
    file1.write_text("element1:\n  name: Access\n  requirements:\n    - Use RBAC\n", encoding="utf-8")
    file2.write_text(
        "element1:\n  name: Encryption\n  requirements:\n    - Enable TLS\n",
        encoding="utf-8",
    )

    yaml1, yaml2 = task2_comparator.load_yaml_files(str(file1), str(file2))

    assert yaml1["element1"]["name"] == "Access"
    assert yaml2["element1"]["name"] == "Encryption"


def test_compare_kde_names_writes_sorted_rows(tmp_path):
    output_file = tmp_path / "name_diffs.txt"
    yaml1 = {
        "element1": {"name": "Encryption", "requirements": ["Enable TLS"]},
        "element2": {"name": "Users", "requirements": ["Use MFA"]},
    }
    yaml2 = {
        "element1": {"name": "Encryption", "requirements": ["Enable TLS"]},
        "element2": {"name": "Network", "requirements": ["Segment traffic"]},
    }

    task2_comparator.compare_kde_names(
        yaml1,
        yaml2,
        "doc1-kdes.yaml",
        "doc2-kdes.yaml",
        str(output_file),
    )

    lines = output_file.read_text(encoding="utf-8").strip().splitlines()
    assert lines == [
        "Users,ABSENT-IN-doc2-kdes.yaml,PRESENT-IN-doc1-kdes.yaml",
        "Network,ABSENT-IN-doc1-kdes.yaml,PRESENT-IN-doc2-kdes.yaml",
    ]


def test_compare_kde_requirements_writes_readme_tuple_format(tmp_path):
    output_file = tmp_path / "requirement_diffs.txt"
    yaml1 = {
        "element1": {"name": "Encryption", "requirements": ["Enable TLS", "Rotate certs"]},
        "element2": {"name": "Logging", "requirements": ["Collect audit logs"]},
    }
    yaml2 = {
        "element1": {"name": "Encryption", "requirements": ["Enable TLS"]},
        "element2": {"name": "Network", "requirements": ["Segment traffic"]},
    }

    task2_comparator.compare_kde_requirements(
        yaml1,
        yaml2,
        "doc1-kdes.yaml",
        "doc2-kdes.yaml",
        str(output_file),
    )

    lines = output_file.read_text(encoding="utf-8").strip().splitlines()
    assert lines == [
        "Encryption,ABSENT-IN-doc2-kdes.yaml,PRESENT-IN-doc1-kdes.yaml,Rotate certs",
        "Logging,ABSENT-IN-doc2-kdes.yaml,PRESENT-IN-doc1-kdes.yaml,NA",
        "Network,ABSENT-IN-doc1-kdes.yaml,PRESENT-IN-doc2-kdes.yaml,NA",
    ]
