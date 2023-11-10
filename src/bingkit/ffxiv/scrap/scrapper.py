from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import TypedDict

import pandas as pd
from tqdm.auto import tqdm

if sys.version_info >= (3, 11):
    import asyncio.taskgroups as taskgroups
else:
    import taskgroups as taskgroups

KO_BASE_URL = (
    "https://raw.githubusercontent.com/Ra-Workspace/ffxiv-datamining-ko/master/csv"
)
EN_BASE_URL = "https://raw.githubusercontent.com/xivapi/ffxiv-datamining/master/csv"
here = Path(__file__).parent


class TaskDict(TypedDict):
    en: list[asyncio.Task[pd.DataFrame]]
    ko: list[asyncio.Task[pd.DataFrame]]


async def url_to_df(name: str, columns: list[str], lang: str) -> pd.DataFrame:
    base_url = KO_BASE_URL if lang == "ko" else EN_BASE_URL
    url = f"{base_url}/{name}.csv"
    columns = ["#", *columns]

    df = await asyncio.to_thread(
        pd.read_csv,
        url,
        usecols=columns,
        skiprows=[0, 2],
        index_col=0,
        low_memory=False,
    )

    rename = {col: f"{col}_{lang}" for col in columns}
    df.rename(columns=rename, inplace=True)
    return df


async def download(config: dict[str, list[str]]) -> TaskDict:
    pbar1 = tqdm(total=len(config) * 2, desc="Scraping")
    tasks = TaskDict({"en": [], "ko": []})

    async with taskgroups.TaskGroup() as tg:
        for lang in ("en", "ko"):
            for name, columns in config.items():
                task = tg.create_task(url_to_df(name, columns, lang), name=name)
                tasks[lang].append(task)
                task.add_done_callback(lambda _: pbar1.update(1))

    return tasks


async def concat_and_save(tasks: TaskDict, save_dir: Path) -> None:
    pbar2 = tqdm(total=len(tasks["en"]), desc="Saving")
    save_dir.mkdir(exist_ok=True)

    async with taskgroups.TaskGroup() as tg:
        for task_en, task_ko in zip(tasks["en"], tasks["ko"], strict=True):
            en, ko = task_en.result(), task_ko.result()
            name = task_en.get_name()
            df = pd.concat([en, ko], axis=1)

            save_path = save_dir.joinpath(f"{name}.xlsx")
            task = tg.create_task(asyncio.to_thread(df.to_excel, save_path))
            task.add_done_callback(lambda _: pbar2.update(1))


async def scrap(
    config_path: str | Path | None = None, save_dir: str | Path | None = None
):
    config_path = (
        here.joinpath("default.json") if config_path is None else Path(config_path)
    )
    config: dict[str, list[str]] = json.loads(config_path.read_bytes())
    save_dir = Path().cwd().joinpath("data") if save_dir is None else Path(save_dir)

    tasks = await download(config)
    await concat_and_save(tasks, save_dir)
