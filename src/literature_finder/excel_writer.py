"""Simple compatible XLSX export with exactly the requested eight columns."""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

from .models import LiteratureRecord

HEADERS = ["序号", "文献类型", "文献名", "文献发表日期", "期刊/来源", "DOI号", "链接", "备注"]


def write_excel(records: list[LiteratureRecord], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Literature"
    sheet.append(HEADERS)
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for index, record in enumerate(records, 1):
        sheet.append([index, record.literature_type or "其他", record.title, record.publication_date or "", record.source or "", record.doi or "", record.best_access_url or "", record.notes or ""])
        link_cell = sheet.cell(index + 1, 7)
        if record.best_access_url:
            link_cell.hyperlink = record.best_access_url
            link_cell.style = "Hyperlink"
        sheet.cell(index + 1, 6).number_format = "@"
        sheet.cell(index + 1, 4).number_format = "@"
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    widths = [8, 14, 52, 18, 28, 28, 52, 44]
    for index, width in enumerate(widths, 1):
        sheet.column_dimensions[get_column_letter(index)].width = width
    workbook.save(output)
    return output

