import asyncio
import asyncio.taskgroups as taskgroups
import json
import os
from pathlib import Path

import polars as pl
import polars.selectors as cs
from tqdm.auto import tqdm


def get_rsv_mapping(path: str | os.PathLike[str]) -> dict[str, str]:
    with Path(path).open("rb") as file:
        return json.load(file)


async def replace_one(path: str | os.PathLike[str], rsv_mapping: dict[str, str]):
    df = await asyncio.to_thread(pl.read_excel, Path(path))
    df = df.with_columns(cs.string().replace(rsv_mapping))
    await asyncio.to_thread(df.write_excel, Path(path))


async def replace(
    data_dir: str | os.PathLike[str] | None = None,
    rsv_path: str | os.PathLike[str] | None = None,
):
    data_dir = Path("data") if data_dir is None else Path(data_dir)
    rsv_path = Path("rsv.json") if rsv_path is None else Path(rsv_path)

    if not rsv_path.exists():
        msg = f"{rsv_path!r} does not exist"
        raise FileNotFoundError(msg)

    rsv_mapping = get_rsv_mapping(rsv_path)
    files = list(data_dir.rglob("*.xlsx"))
    pbar = tqdm(total=len(files), desc="RSV Replacing")
    async with taskgroups.TaskGroup() as tg:
        for path in files:
            coro = replace_one(path, rsv_mapping)
            task = tg.create_task(coro)
            task.add_done_callback(lambda _: pbar.update(1))
    pbar.close()
