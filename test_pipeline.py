from __future__ import annotations

from zipfile import ZipFile

import pandas as pd

import pipeline as main
def _chat_response(content: str):
    return [[{"generated_text": [{"role": "assistant", "content": content}]}]]


class SmokeLLM:
    def __call__(self, payload, max_new_tokens=512):  # noqa: ARG002
        if isinstance(payload, list):
            prompt = payload[0][1]["content"][0]["text"]
        else:
            prompt = payload

        if "cis-r1.pdf" in prompt:
            return _chat_response(
                "element1:\n  name: Encryption\n  requirements:\n    - Enable TLS\n"
            )
        return _chat_response(
            "element1:\n  name: Access Control\n  requirements:\n    - Review RBAC\n"
        )


def test_run_pipeline_for_pair_creates_expected_artifacts(monkeypatch, tmp_path, make_pdf):
    pdf1 = make_pdf("cis-r1.pdf", "Use TLS everywhere")
    pdf2 = make_pdf("cis-r2.pdf", "Review RBAC quarterly")
    yaml_seed = tmp_path / "resource.yaml"
    yaml_seed.write_text("apiVersion: v1\nkind: ConfigMap\n", encoding="utf-8")
    yaml_zip = tmp_path / "project-yamls.zip"
    with ZipFile(yaml_zip, "w") as archive:
        archive.write(yaml_seed, arcname="resource.yaml")

    def fake_execute_kubescape(controls, yaml_zip_path):
        assert yaml_zip_path == str(yaml_zip)
        assert controls == ["C-0002", "C-0007", "C-0035", "C-0065", "C-0066"]
        return pd.DataFrame(
            [
                {
                    "FilePath": "resource.yaml",
                    "Severity": "High",
                    "Control name": "Review RBAC",
                    "Failed resources": 1,
                    "All Resources": 3,
                    "Compliance score": 66,
                }
            ]
        )

    monkeypatch.setattr(main.task3_executor, "execute_kubescape", fake_execute_kubescape)

    result = main.run_pipeline_for_pair(
        pdf1=str(pdf1),
        pdf2=str(pdf2),
        output_root=tmp_path / "outputs",
        project_yamls_zip=str(yaml_zip),
        llm_pipe=SmokeLLM(),
    )

    for key in (
        "llm_output_file",
        "yaml_1",
        "yaml_2",
        "name_differences",
        "requirement_differences",
        "controls_file",
        "csv_file",
    ):
        assert result[key]

    assert (tmp_path / "outputs" / "cis-r1_vs_cis-r2" / "kubescape_results.csv").exists()
