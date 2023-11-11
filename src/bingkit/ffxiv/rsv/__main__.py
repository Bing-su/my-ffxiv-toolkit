from __future__ import annotations

import fileinput
import glob
import json
import re
from pathlib import Path
from typing import NamedTuple


class RSVData(NamedTuple):
    key: str
    value: str


def is_rsv_line(line: str) -> bool:
    return line.startswith("262|")


def parse_rsv_line(line: str) -> RSVData:
    _net, _time, _lang, _id, key, value, _hash = line.split("|")
    value = re.sub(r"[]+", "\n", value)
    return RSVData(key, value)


def convert_files(patterns: list[str]) -> list[Path]:
    return [
        p
        for pattern in patterns
        for file in glob.glob(pattern)  # noqa: PTH207
        if (p := Path(file)).is_file()
    ]


def parse_log(file_patterns: list[str], save_path: str | Path | None):
    save_path = Path("rsv.json") if save_path is None else Path(save_path)
    mapping = {}

    converted_files = convert_files(file_patterns)
    if not converted_files:
        return

    with fileinput.input(files=converted_files, encoding="utf-8") as files:
        for line in files:
            if not is_rsv_line(line):
                continue
            rsv = parse_rsv_line(line)
            mapping[rsv.key] = rsv.value

    with save_path.open("w", encoding="utf-8") as file:
        json.dump(mapping, file, indent=2, ensure_ascii=False)
