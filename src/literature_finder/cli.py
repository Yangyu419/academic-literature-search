"""Command-line entry point for the two-phase search/download workflow."""

from __future__ import annotations

import argparse
import csv
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

from .clarification import clarification_prompt
from .download import DownloadManager
from .downloader import parse_selection
from .excel_writer import write_excel
from .persistence import load_records, save_records
from .pipeline import run_search
from .query_planner import parse_request


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    # Preserve the original `literature-search "topic"` invocation.
    if raw and raw[0] not in {"search", "download", "-h", "--help"}:
        raw.insert(0, "search")
    parser = _parser()
    args = parser.parse_args(raw)
    logging.basicConfig(level=getattr(logging, args.log_level), format="[%(levelname)s] %(message)s")
    if args.command == "search":
        return _search(args)
    return _download(args)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="检索公开学术来源并导出合法文献清单。")
    sub = parser.add_subparsers(dest="command", required=True)
    search = sub.add_parser("search", help="多源检索并导出 Excel，不自动下载")
    search.add_argument("topic", help="研究主题或研究问题")
    search.add_argument("--target", type=int, default=30, help="最终保留数量，默认 30，范围 1-200")
    search.add_argument("--output-dir", default=".", help="检索输出目录")
    search.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    download = sub.add_parser("download", help="在用户明确选择后下载已确认的合法全文")
    download.add_argument("workbook", help="检索阶段生成的 Excel 路径")
    download.add_argument("--selection", default=None, help="序号或范围，例如 1,3,8-12；不填表示全部")
    download.add_argument("--type", dest="type_filter", default=None, help="文献类型，逗号分隔")
    download.add_argument("--threshold", type=float, default=None, help="相关性评分下限")
    download.add_argument("--start-year", type=int, default=None)
    download.add_argument("--end-year", type=int, default=None)
    download.add_argument("--force-redownload", action="store_true", help="显式忽略本地存在检查并重新下载")
    download.add_argument("--resume", action="store_true", help="只重试 download_report.csv 中上次失败或无效的记录")
    download.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    return parser


def _search(args: argparse.Namespace) -> int:
    request = parse_request(args.topic, target_count=max(1, min(200, args.target)))
    prompt = clarification_prompt(request)
    if prompt:
        print(prompt)
        return 2

    root = Path(args.output_dir)
    root.mkdir(parents=True, exist_ok=True)
    (root / "logs").mkdir(exist_ok=True)
    log_path = root / "logs" / "retrieval.log"
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logging.getLogger().addHandler(file_handler)
    plan, result = run_search(request)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    workbook = root / f"literature_search_{stamp}.xlsx"
    records_json = root / "metadata" / f"records_{stamp}.json"
    write_excel(result.records, workbook)
    save_records(result.records, records_json)
    save_records(result.records, root / "metadata" / "records.json")
    print(f"检索完成：原始候选 {result.raw_candidate_count}，去重后/最终保留 {len(result.records)}")
    print(f"合法公开下载入口：{sum(record.download_permission_verified for record in result.records)}")
    print(f"Excel：{workbook}")
    print(f"内部记录：{records_json}")
    print("下一步：仅保留 Excel，或在用户明确选择后运行 literature-search download；不会自动下载。")
    if result.failures:
        print("失败或跳过来源：" + "; ".join(f"{item.source}: {item.error}" for item in result.failures))
    return 0


def _download(args: argparse.Namespace) -> int:
    workbook = Path(args.workbook)
    if not workbook.exists():
        print(f"找不到 Excel：{workbook}", file=sys.stderr)
        return 2
    records_path = _find_records(workbook)
    if records_path is None:
        print("Excel 旁未找到内部 records JSON；请保留检索输出目录中的 metadata 文件。", file=sys.stderr)
        return 2
    records = load_records(records_path)
    log_dir = workbook.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(log_dir / "retrieval.log", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logging.getLogger().addHandler(file_handler)
    selected = parse_selection(args.selection, len(records)) if args.selection else None
    if args.resume:
        failed = _failed_sequences(workbook.parent / "download_report.csv")
        selected = failed if selected is None else selected & failed
        print(f"断点续传：仅重试 {len(selected)} 篇上次失败或 PDF 无效的记录")
    type_filter = {item.strip() for item in re.split(r"[,，]", args.type_filter) if item.strip()} if args.type_filter else None
    results = DownloadManager().download(
        records, workbook.parent, selected=selected, type_filter=type_filter,
        relevance_threshold=args.threshold, start_year=args.start_year, end_year=args.end_year,
        force_redownload=args.force_redownload,
    )
    write_excel(records, workbook)
    save_records(records, records_path)
    counts = {status: sum(item.status == status for item in results) for status in {item.status for item in results}}
    print(f"计划处理：{len(results)} 篇")
    print(f"成功新下载：{counts.get('downloaded', 0)} 篇")
    print(f"本地已有，已跳过：{counts.get('skipped_existing', 0)} 篇")
    print(f"下载后发现重复：{counts.get('skipped_duplicate', 0)} 篇")
    print(f"没有合法全文：{counts.get('unavailable', 0)} 篇")
    print(f"下载失败或 PDF 无效：{counts.get('failed', 0) + counts.get('invalid_pdf', 0)} 篇")
    print(f"报告：{workbook.parent / 'download_report.csv'}")
    return 0


def _find_records(workbook: Path) -> Path | None:
    candidates = [
        workbook.with_suffix(".records.json"),
        workbook.parent / "metadata" / "records.json",
        workbook.parent / "records.json",
    ]
    return next((path for path in candidates if path.exists()), None)


def _failed_sequences(report: Path) -> set[int]:
    """Read only retryable rows; successful rows are never selected by resume."""
    if not report.exists():
        return set()
    retryable = {"failed", "invalid_pdf", "corrupt"}
    try:
        with report.open("r", newline="", encoding="utf-8-sig") as handle:
            return {
                int(row["序号"])
                for row in csv.DictReader(handle)
                if row.get("状态") in retryable and str(row.get("序号", "")).isdigit()
            }
    except (OSError, ValueError, KeyError, TypeError):
        return set()


if __name__ == "__main__":
    raise SystemExit(main())
