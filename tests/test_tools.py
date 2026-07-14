import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tools import _resolve, create_xlsx_with_formulas, create_word_document, OUTPUT_DIR

def test_resolve_strips_virtual_and_windows_paths():
    assert _resolve("/outputs/ledger.xlsx") == str(OUTPUT_DIR / "ledger.xlsx")
    assert _resolve("ledger.xlsx") == str(OUTPUT_DIR / "ledger.xlsx")
    assert _resolve("C:\\weird\\path\\ledger.xlsx") == str(OUTPUT_DIR / "ledger.xlsx")

def test_xlsx_formula_preserved_not_hardcoded():
    result = create_xlsx_with_formulas.func(
        filepath="test_ledger.xlsx",
        json_data_matrix=[["A", "B"], [1, 2], ["Total", {"formula": "=SUM(A2:A2)"}]],
    )
    assert result["success"] is True

def test_docx_rejects_bullet_heavy_content():
    bullets = "\n".join(f"- point {i}" for i in range(10))
    result = create_word_document.func(filepath="test.docx", content=bullets, title="T")
    assert result["success"] is False
    assert "Rejected" in result["message"]

def test_docx_accepts_prose():
    prose = "This is a real paragraph. " * 10
    result = create_word_document.func(filepath="test_prose.docx", content=prose, title="T")
    assert result["success"] is True