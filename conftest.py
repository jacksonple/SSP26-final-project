from __future__ import annotations

import fitz
import pytest


@pytest.fixture
def make_pdf(tmp_path):
    def _make_pdf(name: str, text: str):
        pdf_path = tmp_path / name
        document = fitz.open()
        page = document.new_page()
        page.insert_text((72, 72), text)
        document.save(pdf_path)
        document.close()
        return pdf_path

    return _make_pdf
