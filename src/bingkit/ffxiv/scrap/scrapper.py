from __future__ import annotations

import asyncio
import asyncio.taskgroups as taskgroups
import json
from pathlib import Path

import polars as pl
from tqdm.auto import tqdm

from bingkit.ffxiv._base import BASE_URL, get_csv

here = Path(__file__).parent


async def make_df(name: str, columns: list[str], save_dir: Path) -> None:
    columns = ["#", *columns]
    langs = ("en", "ko")

    tasks = []
    async with taskgroups.TaskGroup() as tg:
        for lang in langs:
            usecols = columns if lang == "en" else columns[1:]
            coro = get_csv(BASE_URL[lang].format(name=name), usecols)
            tasks.append(tg.create_task(coro))

    dfs: list[pl.DataFrame] = [task.result() for task in tasks]
    for i, (lang, df) in enumerate(zip(langs, dfs)):
        rename = {col: f"{col}_{lang}" for col in df.columns}
        rename["#"] = "#"
        dfs[i] = dfs[i].rename(mapping=rename)

    df = pl.concat(dfs, how="horizontal")
    save_path = save_dir.joinpath(f"{name}.xlsx")
    await asyncio.to_thread(df.write_excel, save_path)


async def scrap(
    config_path: str | Path | None = None, save_dir: str | Path | None = None
):
    config_path = (
        here.joinpath("default.json") if config_path is None else Path(config_path)
    )
    config: dict[str, list[str]] = json.loads(config_path.read_bytes())
    save_dir = Path.cwd().joinpath("data") if save_dir is None else Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    pbar = tqdm(total=len(config), desc="Scraping")
    async with taskgroups.TaskGroup() as tg:
        for name, columns in config.items():
            coro = make_df(name, columns, save_dir)
            task = tg.create_task(coro)
            task.add_done_callback(lambda _: pbar.update(1))
    pbar.close()
