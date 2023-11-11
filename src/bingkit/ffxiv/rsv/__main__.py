from __future__ import annotations

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


def parse_log(log_file: str | Path, save_dir: str | Path | None):
    save_dir = Path.cwd() if save_dir is None else Path(save_dir)
    mapping = {}

    with Path(log_file).open("r", encoding="utf-8") as file:
        for line in file:
            if not is_rsv_line(line):
                continue
            rsv = parse_rsv_line(line)
            mapping[rsv.key] = rsv.value

    save_path = save_dir.joinpath("rsv.json")
    with save_path.open("w", encoding="utf-8") as file:
        json.dump(mapping, file, indent=2, ensure_ascii=False)


def cli(log_file: str, save_dir: str = "."):
    parse_log(log_file, save_dir)


if __name__ == "__main__":
    import typer

    typer.run(cli)
