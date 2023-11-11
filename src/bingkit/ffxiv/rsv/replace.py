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


def get_rsv_mapping(path: str | Path) -> dict[str, str]:
    with Path(path).open("rb") as file:
        return json.load(file)


async def replace_one(path: str | Path, rsv_mapping: dict[str, str]):
    df = await asyncio.to_thread(pd.read_excel, path)
    df.replace(rsv_mapping, inplace=True)
    await asyncio.to_thread(df.to_excel, path, index=False)


async def replace(
    data_dir: str | Path | None = None, rsv_path: str | Path | None = None
):
    data_dir = Path("data") if data_dir is None else Path(data_dir)
    rsv_path = Path("rsv.json") if rsv_path is None else Path(rsv_path)

    rsv_mapping = get_rsv_mapping(rsv_path)
    files = list(data_dir.rglob("*.xlsx"))
    pbar = tqdm(total=len(files), desc="RSV Replacing")
    async with taskgroups.TaskGroup() as tg:
        for path in files:
            coro = replace_one(path, rsv_mapping)
            task = tg.create_task(coro)
            task.add_done_callback(lambda _: pbar.update(1))
    pbar.close()
