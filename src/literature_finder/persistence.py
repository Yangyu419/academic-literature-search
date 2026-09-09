"""JSON persistence for internal records used by the second download phase."""

from __future__ import annotations

import json
from dataclasses import asdict, fields
from pathlib import Path
from typing import Any

from .models import LiteratureRecord


def save_records(records: list[LiteratureRecord], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps([asdict(record) for record in records], ensure_ascii=False, indent=2), encoding="utf-8")
    return output


def load_records(path: str | Path) -> list[LiteratureRecord]:
    data: Any = json.loads(Path(path).read_text(encoding="utf-8"))
    allowed = {field.name for field in fields(LiteratureRecord)}
    return [LiteratureRecord(**{key: value for key, value in item.items() if key in allowed}) for item in data]
