from __future__ import annotations

from pathlib import Path

import yaml

import task_1 as task1_extractor


def _chat_response(content: str):
    return [[{"generated_text": [{"role": "assistant", "content": content}]}]]


class StubLLM:
    def __call__(self, payload, max_new_tokens=512):  # noqa: ARG002
        if isinstance(payload, list):
            prompt = payload[0][1]["content"][0]["text"]
        else:
            prompt = payload

        if "cis-r1.pdf" in prompt and "Follow steps 1-4" in prompt:
            return _chat_response(
                "element1:\n  name: Encryption\n  requirements:\n    - Enable TLS\n"
            )
        if "cis-r1.pdf" in prompt and "Example 1:" in prompt:
            return _chat_response(
                "element1:\n  name: Few Shot KDE\n  requirements:\n    - Use strong passwords\n"
            )
        if "cis-r1.pdf" in prompt:
            return _chat_response(
                "element1:\n  name: Zero Shot KDE\n  requirements:\n    - Log access\n"
            )

        if "cis-r2.pdf" in prompt and "Follow steps 1-4" in prompt:
            return _chat_response("not valid yaml")
        if "cis-r2.pdf" in prompt and "Example 1:" in prompt:
            return _chat_response(
                "element1:\n  name: Access Control\n  requirements:\n    - Review RBAC\n"
            )
        return _chat_response(
            "element1:\n  name: Zero Shot Backup\n  requirements:\n    - Back up secrets\n"
        )


def test_load_documents_reads_two_pdfs(make_pdf):
    pdf1 = make_pdf("doc1.pdf", "First security requirement")
    pdf2 = make_pdf("doc2.pdf", "Second security requirement")

    document1, document2 = task1_extractor.load_documents(str(pdf1), str(pdf2))

    assert document1["name"] == "doc1.pdf"
    assert document2["name"] == "doc2.pdf"
    assert "First security requirement" in document1["text"]
    assert "Second security requirement" in document2["text"]


def test_construct_zero_shot_prompt_contains_document_name():
    prompt = task1_extractor.construct_zero_shot_prompt("body text", "cis-r1.pdf")

    assert "cis-r1.pdf" in prompt
    assert "YAML output:" in prompt


def test_construct_few_shot_prompt_contains_examples():
    prompt = task1_extractor.construct_few_shot_prompt("body text", "cis-r1.pdf")

    assert "Example 1:" in prompt
    assert "Example 2:" in prompt
    assert "cis-r1.pdf" in prompt


def test_construct_chain_of_thought_prompt_contains_steps():
    prompt = task1_extractor.construct_chain_of_thought_prompt("body text", "cis-r1.pdf")

    assert "Step 1" in prompt
    assert "Step 4" in prompt
    assert "cis-r1.pdf" in prompt


def test_extract_kdes_for_documents_writes_yaml_and_prefers_fallback_order(tmp_path):
    result = task1_extractor.extract_kdes_for_documents(
        document1={"name": "cis-r1.pdf", "text": "Doc one"},
        document2={"name": "cis-r2.pdf", "text": "Doc two"},
        output_dir=str(tmp_path),
        llm_pipe=StubLLM(),
    )

    yaml_1 = yaml.safe_load(Path(result["yaml_paths"][0]).read_text(encoding="utf-8"))
    yaml_2 = yaml.safe_load(Path(result["yaml_paths"][1]).read_text(encoding="utf-8"))
    llm_output = Path(result["llm_output_file"]).read_text(encoding="utf-8")

    assert result["documents"]["document_1"]["selected_prompt_type"] == "chain_of_thought"
    assert result["documents"]["document_2"]["selected_prompt_type"] == "few_shot"
    assert yaml_1["element1"]["name"] == "Encryption"
    assert yaml_2["element1"]["name"] == "Access Control"
    assert llm_output.count("*Prompt Type*") == 6


def test_save_llm_output_appends_required_sections(tmp_path):
    output_file = tmp_path / "llm_output.txt"

    task1_extractor.save_llm_output(
        llm_name=task1_extractor.LLM_NAME,
        prompt="demo prompt",
        prompt_type="zero_shot",
        llm_output="demo output",
        output_file=str(output_file),
    )

    content = output_file.read_text(encoding="utf-8")
    assert "*LLM Name*" in content
    assert "*Prompt Used*" in content
    assert "*Prompt Type*" in content
    assert "*LLM Output*" in content
