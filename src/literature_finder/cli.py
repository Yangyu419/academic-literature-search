"""Command-line entry point for a reproducible, opt-in search run."""

from __future__ import annotations

import argparse
import logging
from datetime import datetime
from pathlib import Path

from .clarification import clarification_prompt
from .downloader import SafeDownloader, parse_selection
from .excel_writer import write_excel
from .pipeline import run_search
from .query_planner import parse_request


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Search academic sources and export a lawful literature workbook.")
    parser.add_argument("topic", help="Research topic or research question")
    parser.add_argument("--target", type=int, default=30, help="Number of final records, default 30")
    parser.add_argument("--output-dir", default=".", help="Directory for the workbook")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level), format="[%(levelname)s] %(message)s")
    request = parse_request(args.topic, target_count=max(1, min(200, args.target)))
    prompt = clarification_prompt(request)
    if prompt:
        print(prompt)
        return 2
    plan, result = run_search(request)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = Path(args.output_dir) / f"literature_search_{stamp}.xlsx"
    write_excel(result.records, output)
    print(f"检索完成：原始候选 {result.raw_candidate_count}，去重后/最终保留 {len(result.records)}")
    print(f"合法公开下载入口：{sum(record.download_permission_verified for record in result.records)}")
    print(f"Excel：{output}")
    print("下一步：仅保留 Excel，或在用户明确选择后调用 SafeDownloader；不会自动下载。")
    if result.failures:
        print("失败来源：" + "; ".join(f"{item.source}: {item.error}" for item in result.failures))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

