from __future__ import annotations

import importlib
import os
import re
from pathlib import Path
from typing import Any

import yaml

try:
    import fitz

    PDF_BACKEND = "pymupdf"
except ImportError:
    try:
        import pdfplumber

        PDF_BACKEND = "pdfplumber"
    except ImportError:
        PDF_BACKEND = None

LLM_NAME = "google/gemma-3-1b-it"
MAX_TEXT_CHARS = 2500
PROMPT_TYPES = ("zero_shot", "few_shot", "chain_of_thought")

ZERO_SHOT_TEMPLATE = (
    "Identify the key data elements (KDEs) in the security document '{doc_name}'. "
    "For each KDE provide its name and the associated requirements. "
    "Format output as YAML:\n\n"
    "element1:\n"
    "  name: <element name>\n"
    "  requirements:\n"
    "    - <req1>\n"
    "    - <req2>\n\n"
    "Document:\n{doc_text}\n\n"
    "YAML output:"
)

FEW_SHOT_TEMPLATE = (
    "Example 1:\n"
    "Document: '1.1 Users must have unique accounts. 1.2 Passwords must be 12+ characters.'\n"
    "Output:\n"
    "element1:\n"
    "  name: User Accounts\n"
    "  requirements:\n"
    "    - Users must have unique accounts\n"
    "    - Passwords must be 12+ characters\n\n"
    "Example 2:\n"
    "Document: '2.1 All traffic must be encrypted. 2.2 Use TLS 1.2 or higher.'\n"
    "Output:\n"
    "element1:\n"
    "  name: Network Encryption\n"
    "  requirements:\n"
    "    - All traffic must be encrypted\n"
    "    - Use TLS 1.2 or higher\n\n"
    "Now identify KDEs in document '{doc_name}':\n"
    "{doc_text}\n\n"
    "Output YAML:"
)

CHAIN_OF_THOUGHT_TEMPLATE = (
    "Analyze security document '{doc_name}' step by step.\n\n"
    "Step 1: List all distinct security topics in the document.\n"
    "Step 2: For each topic, collect all related requirements.\n"
    "Step 3: Assign each topic a short descriptive name (the KDE name).\n"
    "Step 4: Output the result as YAML:\n\n"
    "element1:\n"
    "  name: <KDE name>\n"
    "  requirements:\n"
    "    - <requirement>\n\n"
    "Document:\n{doc_text}\n\n"
    "Follow steps 1-4 and produce the YAML output:"
)


def load_documents(file1: str, file2: str) -> tuple[dict[str, str], dict[str, str]]:
    """Load and validate two PDF documents."""

    return (_load_document(file1), _load_document(file2))


def construct_zero_shot_prompt(doc_text: str, doc_name: str) -> str:
    """Construct the zero-shot prompt for a document."""

    return ZERO_SHOT_TEMPLATE.format(doc_name=doc_name, doc_text=doc_text[:MAX_TEXT_CHARS])


def construct_few_shot_prompt(doc_text: str, doc_name: str) -> str:
    """Construct the few-shot prompt for a document."""

    return FEW_SHOT_TEMPLATE.format(doc_name=doc_name, doc_text=doc_text[:MAX_TEXT_CHARS])


def construct_chain_of_thought_prompt(doc_text: str, doc_name: str) -> str:
    """Construct the chain-of-thought prompt for a document."""

    return CHAIN_OF_THOUGHT_TEMPLATE.format(doc_name=doc_name, doc_text=doc_text[:MAX_TEXT_CHARS])


def extract_kdes_for_documents(
    document1: dict[str, str],
    document2: dict[str, str],
    output_dir: str = ".",
    llm_pipe: Any | None = None,
    llm_name: str = LLM_NAME,
    llm_output_file: str | None = None,
) -> dict[str, Any]:
    """Run all prompt types against both documents and save canonical KDE YAML outputs."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    log_path = Path(llm_output_file) if llm_output_file else output_path / "llm_output.txt"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("", encoding="utf-8")

    pipe = llm_pipe or _build_llm_pipeline()
    prompt_builders = {
        "zero_shot": construct_zero_shot_prompt,
        "few_shot": construct_few_shot_prompt,
        "chain_of_thought": construct_chain_of_thought_prompt,
    }
    duplicate_names = document1["name"] == document2["name"]

    yaml_paths: list[str] = []
    document_results: dict[str, Any] = {}

    for index, document in enumerate((document1, document2), start=1):
        prompt_results: dict[str, Any] = {}
        for prompt_type in PROMPT_TYPES:
            prompt = prompt_builders[prompt_type](document["text"], document["name"])
            raw_output = _run_prompt(pipe, prompt)
            parsed_kdes = _parse_kdes_from_text(raw_output)

            save_llm_output(
                llm_name=llm_name,
                prompt=prompt,
                prompt_type=prompt_type,
                llm_output=raw_output,
                output_file=str(log_path),
            )

            prompt_results[prompt_type] = {
                "prompt": prompt,
                "raw_output": raw_output,
                "parsed_kdes": parsed_kdes,
            }

        selected_prompt_type, selected_kdes = _select_canonical_kdes(prompt_results)
        if selected_kdes is None:
            selected_prompt_type = "chain_of_thought"
            selected_kdes = _fallback_kdes_from_text(
                prompt_results[selected_prompt_type]["raw_output"]
            )

        yaml_path = _save_kdes_to_yaml(
            kdes=selected_kdes,
            doc_name=document["name"],
            output_dir=output_path,
            document_index=index,
            duplicate_names=duplicate_names,
        )
        yaml_paths.append(str(yaml_path))
        document_results[f"document_{index}"] = {
            "name": document["name"],
            "selected_prompt_type": selected_prompt_type,
            "yaml_path": str(yaml_path),
            "prompt_results": prompt_results,
        }

    return {
        "yaml_paths": yaml_paths,
        "llm_output_file": str(log_path),
        "documents": document_results,
    }


def save_llm_output(
    llm_name: str,
    prompt: str,
    prompt_type: str,
    llm_output: str,
    output_file: str,
) -> str:
    """Append a single LLM run to the assignment-required text file."""

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8") as handle:
        handle.write(f"*LLM Name*\n{llm_name}\n\n")
        handle.write(f"*Prompt Used*\n{prompt}\n\n")
        handle.write(f"*Prompt Type*\n{prompt_type}\n\n")
        handle.write(f"*LLM Output*\n{llm_output}\n\n")
        handle.write("=" * 80 + "\n\n")
    return str(output_path)


def _load_document(file_path: str) -> dict[str, str]:
    if PDF_BACKEND is None:
        raise ImportError("No PDF backend is available. Install PyMuPDF to load PDF files.")

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a .pdf file, got: {path.suffix}")
    if path.stat().st_size == 0:
        raise ValueError(f"PDF file is empty: {file_path}")

    return {
        "path": str(path.resolve()),
        "name": path.name,
        "text": _extract_pdf_text(path),
    }


def _extract_pdf_text(path: Path) -> str:
    text_parts: list[str] = []

    if PDF_BACKEND == "pymupdf":
        document = fitz.open(str(path))
        if document.page_count == 0:
            raise ValueError(f"PDF has no pages: {path}")
        for page in document:
            text_parts.append(page.get_text())
        document.close()
    else:
        with pdfplumber.open(str(path)) as document:
            if len(document.pages) == 0:
                raise ValueError(f"PDF has no pages: {path}")
            for page in document.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

    text = "\n".join(part for part in text_parts if part and part.strip())
    if not text.strip():
        raise ValueError(f"No text extracted from: {path}")
    return text


def _build_llm_pipeline() -> Any:
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

    transformers = importlib.import_module("transformers")
    torch = importlib.import_module("torch")
    pipeline = getattr(transformers, "pipeline")

    pipeline_kwargs: dict[str, Any] = {
        "task": "text-generation",
        "model": LLM_NAME,
        "torch_dtype": torch.bfloat16 if torch.cuda.is_available() else torch.float32,
    }

    if torch.cuda.is_available():
        pipeline_kwargs["device_map"] = "auto"
    else:
        pipeline_kwargs["device"] = -1

    return pipeline(**pipeline_kwargs)


def _run_prompt(llm_pipe: Any, prompt: str) -> str:
    messages = [
        [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "You are a security document analyzer. Output KDEs as YAML.",
                    }
                ],
            },
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}],
            },
        ]
    ]

    try:
        output = llm_pipe(messages, max_new_tokens=512)
    except Exception:
        output = llm_pipe(prompt, max_new_tokens=512)

    return _extract_generated_text(output)


def _extract_generated_text(output: Any) -> str:
    if isinstance(output, str):
        return output

    if isinstance(output, list) and output:
        first_item = output[0]
        if isinstance(first_item, list) and first_item:
            first_item = first_item[0]
        if isinstance(first_item, dict):
            generated_text = first_item.get("generated_text")
            if isinstance(generated_text, str):
                return generated_text
            if isinstance(generated_text, list) and generated_text:
                last_item = generated_text[-1]
                if isinstance(last_item, dict) and "content" in last_item:
                    return str(last_item["content"])
                return str(last_item)
    return str(output)


def _select_canonical_kdes(prompt_results: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
    for prompt_type in ("chain_of_thought", "few_shot", "zero_shot"):
        parsed_kdes = prompt_results[prompt_type]["parsed_kdes"]
        if parsed_kdes:
            return prompt_type, parsed_kdes
    return "chain_of_thought", None


def _parse_kdes_from_text(text: str) -> dict[str, Any] | None:
    cleaned_text = text.strip()
    if not cleaned_text:
        return None

    direct_parse = _normalize_kde_dict(_safe_yaml_load(cleaned_text))
    if direct_parse:
        return direct_parse

    fenced_blocks = re.findall(r"```(?:yaml)?\s*([\s\S]+?)```", cleaned_text, re.IGNORECASE)
    for block in fenced_blocks:
        parsed_block = _normalize_kde_dict(_safe_yaml_load(block))
        if parsed_block:
            return parsed_block

    element_pattern = re.compile(
        r"(element\d+):\s*\n\s*name:\s*(.+?)\s*\n\s*requirements:\s*\n((?:\s*-\s*.+\n?)*)",
        re.IGNORECASE,
    )
    matches = list(element_pattern.finditer(cleaned_text))
    if not matches:
        return None

    parsed: dict[str, Any] = {}
    for index, match in enumerate(matches, start=1):
        requirements = [
            line.strip().lstrip("- ").strip("\"'")
            for line in match.group(3).splitlines()
            if line.strip()
        ]
        parsed[f"element{index}"] = {
            "name": match.group(2).strip().strip("\"'"),
            "requirements": requirements,
        }
    return parsed or None


def _safe_yaml_load(text: str) -> Any:
    try:
        return yaml.safe_load(text)
    except Exception:
        return None


def _normalize_kde_dict(candidate: Any) -> dict[str, Any] | None:
    if not isinstance(candidate, dict):
        return None

    normalized: dict[str, Any] = {}
    for index, (key, value) in enumerate(candidate.items(), start=1):
        if not isinstance(value, dict):
            continue

        name = str(value.get("name", key)).strip()
        requirements = _normalize_requirements(value.get("requirements"))
        if not name:
            continue

        normalized[f"element{index}"] = {
            "name": name,
            "requirements": requirements,
        }

    return normalized or None


def _normalize_requirements(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, (list, tuple, set)):
        values = list(value)
    else:
        values = [str(value)]

    cleaned = [str(item).strip() for item in values if str(item).strip()]
    return cleaned


def _fallback_kdes_from_text(raw_output: str) -> dict[str, Any]:
    summary = raw_output.strip().replace("\n", " ")
    if not summary:
        summary = "LLM returned no parseable KDEs."

    return {
        "element1": {
            "name": "Security Requirements",
            "requirements": [summary[:200]],
        }
    }


def _save_kdes_to_yaml(
    kdes: dict[str, Any],
    doc_name: str,
    output_dir: Path,
    document_index: int,
    duplicate_names: bool,
) -> Path:
    base_name = Path(doc_name).stem
    file_name = f"{base_name}-kdes.yaml"
    if duplicate_names:
        file_name = f"doc{document_index}-{base_name}-kdes.yaml"

    output_path = output_dir / file_name
    with output_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(kdes, handle, sort_keys=False, allow_unicode=True)
    return output_path


__all__ = [
    "LLM_NAME",
    "PROMPT_TYPES",
    "load_documents",
    "construct_zero_shot_prompt",
    "construct_few_shot_prompt",
    "construct_chain_of_thought_prompt",
    "extract_kdes_for_documents",
    "save_llm_output",
]
