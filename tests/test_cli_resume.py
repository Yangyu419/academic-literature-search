from pathlib import Path

from literature_finder.cli import _failed_sequences


def test_resume_only_selects_retryable_failures(tmp_path: Path):
    report = tmp_path / "download_report.csv"
    report.write_text(
        "序号,文献名,状态,文件名,来源链接,失败原因\n"
        "1,success,downloaded,001.pdf,url,\n"
        "2,failed,failed,002.pdf,url,timeout\n"
        "3,bad,invalid_pdf,003.pdf,url,bad header\n"
        "4,skip,skipped_existing,004.pdf,url,\n",
        encoding="utf-8-sig",
    )
    assert _failed_sequences(report) == {2, 3}
