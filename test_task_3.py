from __future__ import annotations

import json
from types import SimpleNamespace
from zipfile import ZipFile

import pandas as pd

import task_3 as task3_executor


def test_load_text_files_reads_two_outputs(tmp_path):
    file1 = tmp_path / "names.txt"
    file2 = tmp_path / "requirements.txt"
    file1.write_text("content one\n", encoding="utf-8")
    file2.write_text("content two\n", encoding="utf-8")

    text1, text2 = task3_executor.load_text_files(str(file1), str(file2))

    assert text1 == "content one\n"
    assert text2 == "content two\n"


def test_map_differences_to_controls_writes_expected_control_file(tmp_path):
    output_file = tmp_path / "kubescape_controls.txt"

    controls = task3_executor.map_differences_to_controls(
        "Encryption,ABSENT-IN-a,PRESENT-IN-b",
        "Access,ABSENT-IN-a,PRESENT-IN-b,password",
        str(output_file),
    )

    content = output_file.read_text(encoding="utf-8").strip().splitlines()
    assert "C-0007" in controls
    assert "C-0012" in controls
    assert content == controls


def test_execute_kubescape_parses_mocked_json(monkeypatch, tmp_path):
    yaml_file = tmp_path / "resource.yaml"
    yaml_file.write_text("apiVersion: v1\nkind: ConfigMap\n", encoding="utf-8")
    yaml_zip = tmp_path / "project-yamls.zip"
    with ZipFile(yaml_zip, "w") as archive:
        archive.write(yaml_file, arcname="resource.yaml")

    payload = {
        "results": [
            {
                "name": "demo-framework",
                "controls": [
                    {
                        "name": "No privileged containers",
                        "numberOfFailedResources": 1,
                        "numberOfAllResources": 3,
                        "complianceScore": 66,
                        "severity": {"scoreFactor": "High"},
                    }
                ],
            }
        ]
    }

    monkeypatch.setattr(task3_executor, "_kubescape_available", lambda: True)
    monkeypatch.setattr(
        task3_executor.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(  # noqa: ARG005
            returncode=0,
            stdout=json.dumps(payload),
            stderr="",
        ),
    )

    df = task3_executor.execute_kubescape(["C-0007"], str(yaml_zip))

    assert list(df.columns) == task3_executor.CSV_COLUMNS
    assert df.iloc[0]["Control name"] == "No privileged containers"
    assert df.iloc[0]["Severity"] == "High"


def test_generate_csv_writes_required_headers(tmp_path):
    output_file = tmp_path / "results.csv"
    df = pd.DataFrame(
        [
            {
                "FilePath": "demo-framework",
                "Severity": "High",
                "Control name": "No privileged containers",
            }
        ]
    )

    task3_executor.generate_csv(df, str(output_file))

    content = output_file.read_text(encoding="utf-8").splitlines()
    assert content[0] == ",".join(task3_executor.CSV_COLUMNS)
    assert "No privileged containers" in content[1]
