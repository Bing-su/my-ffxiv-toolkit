import argparse
from pathlib import Path

import pandas as pd
from tqdm import tqdm


def rsv_replace(rsv: str):
    mapping: dict[str, str] = {}

    with open(rsv, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("_rsv_"):
                continue
            key, value = line.split("|", maxsplit=1)
            value = value.replace("", " ")
            mapping[key] = value

    xlsxs = list(Path("data").rglob("*.xlsx"))
    for xlsx in tqdm(xlsxs):
        df = pd.read_excel(xlsx)
        df = df.replace(mapping)
        df.to_excel(xlsx, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("rsv", type=str, help="path to rsv.txt")
    args = parser.parse_args()
    rsv_replace(args.rsv)
