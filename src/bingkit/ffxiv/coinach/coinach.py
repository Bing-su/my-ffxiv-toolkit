from __future__ import annotations

import re
import shutil
import subprocess
from functools import cache
from pathlib import Path
from types import SimpleNamespace
from urllib.request import urlretrieve

import pandas as pd
from loguru import logger
from tqdm import tqdm

COINACH_PATH = "D:\\SaintCoinach"
COINACH_EXE = "D:\\SaintCoinach\\SaintCoinach.Cmd.exe"
KO = "https://raw.githubusercontent.com/Ra-Workspace/ffxiv-datamining-ko/master/csv/{name}.csv"
CN = "https://raw.githubusercontent.com/thewakingsands/ffxiv-datamining-cn/master/{name}.csv"
CLIENT_GLOBAL = (
    "D:\\Program Files (x86)\\SquareEnix\\FINAL FANTASY XIV - A Realm Reborn"
)
CLIENT_KO = "C:\\Nexon\\FINAL FANTASY XIV - KOREA"

LANG = SimpleNamespace()
LANG.all = ("en", "de", "fr", "ja", "cn", "ko")
LANG.coinach = LANG.all[:4]


mapping = {
    "Action": ["Name"],
    "BNpcName": ["Singular"],
    "Balloon": ["Dialogue"],
    "Completion": ["Text", "GroupTitle"],
    "DynamicEvent": ["Name", "Description"],
    "Fate": ["Name", "Description"],
    "InstanceContentTextData": ["Text"],
    "LogMessage": ["Text"],
    "NpcYell": ["Text"],
    "PlaceName": ["Name"],
    "PublicContentTextData": ["TextData"],
    "Status": ["Name", "Description"],
}


def fix_game_ver(root: Path, ver: str) -> None:
    gamever = root.joinpath("Definitions", "game.ver")
    before = gamever.read_text("utf-8")
    gamever.write_text(ver, encoding="utf-8")
    logger.info(f"before: {before!r} → after: {ver!r}")


def run_coinach(output: Path, name: str):
    cmd = [COINACH_EXE, CLIENT_GLOBAL, f"allexd {name}"]
    subprocess.run(cmd, cwd=COINACH_PATH)
    ver = get_current_ver(COINACH_PATH)
    output_dir = Path(COINACH_PATH).joinpath(ver, "exd-all")
    for output_file in output_dir.glob(f"{name}*.csv"):
        filename = output_file.name
        copy_path = output.joinpath(filename)
        shutil.copyfile(output_file, copy_path)
        logger.info(f"csv saved at {copy_path}")


@cache
def get_current_ver(path: str | Path) -> str:
    candidate = []
    for file in Path(path).iterdir():
        if re.match(r"\d+", file.name):
            candidate.append(file.name)
    if candidate:
        return max(candidate)
    msg = "no game ver found"
    raise RuntimeError(msg)


def fetch(output: Path, name: str, add_cn_ko: bool = True):
    total = len(LANG.all) if add_cn_ko else len(LANG.coinach)
    pbar = tqdm(total=total)

    run_coinach(output, name)
    pbar.update(4)

    if not add_cn_ko:
        return

    for ln, base in [("cn", CN), ("ko", KO)]:
        url = base.format(name=name)
        name_with_lang = f"{name}.{ln}.csv"
        file_path = output.joinpath(name_with_lang)
        urlretrieve(url, file_path)
        logger.info(f"csv saved at {file_path}")
        pbar.update()

    pbar.close()


def concat(output: Path, name: str):
    csv_files = list(output.glob(f"{name}*.csv"))
    csv_files.sort(key=lambda x: LANG.all.index(x.stem.split(".")[-1]))
    use_cols = mapping[name]
    dfs = []
    for file in csv_files:
        df = pd.read_csv(file, skiprows=[0, 2], usecols=use_cols, low_memory=False)
        ln = file.stem.split("_")[-1]
        df = df.rename(columns={col: f"{col}_{ln}" for col in df.columns})
        dfs.append(df)
    all_df = pd.concat(dfs, axis=1)
    save_path = output.joinpath(f"{name}.all.xlsx")
    all_df.to_excel(save_path, index=False)


def main(output: Path, name: str):
    output.mkdir(parents=True, exist_ok=True)
    fetch(output, name)
    concat(output, name)
