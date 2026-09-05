from pathlib import Path

from openpyxl import load_workbook

from literature_finder.excel_writer import HEADERS, write_excel
from literature_finder.link_resolver import BestLegalAccessResolver
from literature_finder.models import LiteratureRecord


def test_arxiv_verified_download_is_preserved():
    record = LiteratureRecord("A preprint", open_access_url="https://arxiv.org/abs/1234.5678", publisher_url="https://arxiv.org/abs/1234.5678", download_url="https://arxiv.org/pdf/1234.5678", download_source="arXiv", download_file_type="pdf", download_permission_verified=True)
    BestLegalAccessResolver().resolve(record)
    assert record.best_access_url == "https://arxiv.org/abs/1234.5678"
    assert record.download_permission_verified is True


def test_excel_has_exact_columns_and_hyperlink(tmp_path: Path):
    record = LiteratureRecord("Official title", literature_type="期刊论文", publication_date="2024-01-02", doi="10.1234/test", best_access_url="https://doi.org/10.1234/test")
    output = write_excel([record], tmp_path / "out.xlsx")
    sheet = load_workbook(output).active
    assert [cell.value for cell in sheet[1]] == HEADERS
    assert sheet.freeze_panes == "A2"
    assert sheet.auto_filter.ref == "A1:H2"
    assert sheet[2][5].value == "10.1234/test"
    assert sheet[2][6].hyperlink.target == "https://doi.org/10.1234/test"
