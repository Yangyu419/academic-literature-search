"""Traceable XLSX export retaining the original eight columns plus new fields."""

from __future__ import annotations

from pathlib import Path
import re

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

from .models import LiteratureRecord

HEADERS = [
    "序号", "文献类型", "文献名", "中文名", "文献发表日期", "期刊/来源", "研究内容", "备注",
    "相关性评分", "作者", "年份", "出版商", "DOI", "摘要", "关键词", "是否开放获取",
    "OA状态", "全文版本", "最佳合法获取链接", "PDF链接", "全文来源", "检索数据库", "下载状态",
    "是否本地已存在", "已有文件路径", "本地文件名", "本地文件路径", "重复判断方式", "是否重复", "SHA256",
]


def _is_probably_english_title(title: str) -> bool:
    letters = [character for character in title if character.isalpha()]
    return bool(letters) and not any("\u4e00" <= character <= "\u9fff" for character in title)


def _display_chinese_title(record: LiteratureRecord) -> str:
    if record.title_zh:
        return record.title_zh
    if _is_probably_english_title(record.title):
        return "未翻译，需人工补充"
    return record.title


def _display_research_content(record: LiteratureRecord) -> str:
    if record.research_content:
        return record.research_content
    if record.abstract:
        # Keep a bounded, readable fallback without inventing content.  The
        # search agent should provide a concise summary when an abstract exists;
        # otherwise retain at most the first three abstract sentences.
        compact = " ".join(record.abstract.split())
        sentences = [part.strip() for part in re.split(r"(?<=[。！？.!?])\s*", compact) if part.strip()]
        summary = " ".join(sentences[:3]) if sentences else compact
        return summary if len(summary) <= 240 else summary[:237] + "..."
    return "未获取摘要，需人工补充"


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
        row = [
            index, record.literature_type or "其他", record.title, _display_chinese_title(record),
            record.publication_date or "", record.source or record.journal_or_source or "",
            _display_research_content(record), record.notes or "", record.relevance_score or "",
            "；".join(record.authors), record.year or "", record.publisher or "", record.doi or "",
            record.abstract or "", "；".join(record.keywords), "是" if record.is_open_access else "否",
            record.oa_status or "", record.oa_version or "", record.best_legal_access_url or record.best_access_url or "",
            record.pdf_url or record.download_url or "", record.pdf_source or record.download_source or "",
            "；".join(record.metadata_sources), record.download_status or "pending",
            "是" if record.existing_local_copy else "否", record.existing_local_path or "",
            Path(record.download_path).name if record.download_path else "", record.download_path or "",
            record.duplicate_reason or "", "是" if record.existing_local_copy or record.download_status in {"skipped_existing", "skipped_duplicate"} else "否",
            record.file_hash_sha256 or "",
        ]
        sheet.append(row)
        sheet.cell(index + 1, 5).number_format = "@"
        sheet.cell(index + 1, 11).number_format = "0"
        doi_value = sheet.cell(index + 1, 13).value
        if doi_value:
            sheet.cell(index + 1, 13).hyperlink = f"https://doi.org/{doi_value}"
            sheet.cell(index + 1, 13).style = "Hyperlink"
        for column in (19, 20):
            value = sheet.cell(index + 1, column).value
            if value:
                sheet.cell(index + 1, column).hyperlink = value
                sheet.cell(index + 1, column).style = "Hyperlink"
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    widths = [8, 14, 52, 36, 18, 28, 60, 44, 12, 32, 10, 24, 28, 70, 30, 14, 16, 18, 48, 48, 22, 24, 20, 14, 48, 42, 52, 28, 12, 68]
    for index, width in enumerate(widths, 1):
        sheet.column_dimensions[get_column_letter(index)].width = width
    workbook.save(output)
    return output
