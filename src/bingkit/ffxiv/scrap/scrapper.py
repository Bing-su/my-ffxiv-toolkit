from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pandas as pd
from tqdm.auto import tqdm

if sys.version_info >= (3, 11):
    import asyncio.taskgroups as taskgroups
else:
    import taskgroups as taskgroups

base_url = {
    "en": "https://raw.githubusercontent.com/xivapi/ffxiv-datamining/master/csv",
    "ko": "https://raw.githubusercontent.com/Ra-Workspace/ffxiv-datamining-ko/master/csv",
}
here = Path(__file__).parent


async def read_url(lang: str, name: str, columns: list[str]) -> pd.DataFrame:
    url = f"{base_url[lang]}/{name}.csv"
    return await asyncio.to_thread(
        pd.read_csv,
        url,
        usecols=columns,
        skiprows=[0, 2],
        index_col=0,
        low_memory=False,
    )


async def make_df(name: str, columns: list[str], save_dir: Path) -> None:
    columns = ["#", *columns]
    langs = ("en", "ko")

    tasks = []
    async with taskgroups.TaskGroup() as tg:
        for lang in langs:
            coro = read_url(lang, name, columns)
            tasks.append(tg.create_task(coro))

    dfs = [task.result() for task in tasks]
    for i, lang in enumerate(langs):
        rename = {col: f"{col}_{lang}" for col in columns}
        dfs[i].rename(columns=rename, inplace=True)

    df = pd.concat(dfs, axis=1)
    save_path = save_dir.joinpath(f"{name}.xlsx")
    await asyncio.to_thread(df.to_excel, save_path)


async def scrap(
    config_path: str | Path | None = None, save_dir: str | Path | None = None
):
    config_path = (
        here.joinpath("default.json") if config_path is None else Path(config_path)
    )
    config: dict[str, list[str]] = json.loads(config_path.read_bytes())
    save_dir = Path.cwd().joinpath("data") if save_dir is None else Path(save_dir)

    pbar = tqdm(total=len(config), desc="Scraping")
    async with taskgroups.TaskGroup() as tg:
        for name, columns in config.items():
            coro = make_df(name, columns, save_dir)
            task = tg.create_task(coro)
            task.add_done_callback(lambda _: pbar.update(1))
    pbar.close()
