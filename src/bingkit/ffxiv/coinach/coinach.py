import asyncio
import os
from pathlib import Path

import polars as pl
from loguru import logger
from tqdm.asyncio import tqdm

from bingkit.ffxiv._base import BASE_URL, LANG, SHEETS, get_csv


async def download_csv(url: str, output: str | os.PathLike[str]):
    df = await get_csv(url)
    df.write_csv(Path(output))
    logger.info(f"csv saved at {output}")


async def fetch(output: Path, name: str):
    total = len(LANG)
    pbar = tqdm(total=total)

    async with asyncio.TaskGroup() as tg:
        for lang, baseurl in BASE_URL.items():
            url = baseurl.format(name=name)
            name_with_lang = f"{name}.{lang}.csv"
            file_path = output.joinpath(name_with_lang)
            fut = download_csv(url, file_path)
            tg.create_task(fut).add_done_callback(lambda _: pbar.update())

    pbar.close()


def concat(output: Path, name: str):
    csv_files = list(output.glob(f"{name}*.csv"))
    csv_files.sort(key=lambda x: LANG.index(x.stem.split(".")[-1]))
    use_cols = SHEETS[name]
    dfs = []
    for file in csv_files:
        ln = file.stem.split(".")[-1]
        df = pl.scan_csv(file).select(use_cols)
        columns = df.collect_schema().names()
        df = df.rename(mapping={col: f"{col}_{ln}" for col in columns}).collect()
        dfs.append(df)
    all_df = pl.concat(dfs, how="horizontal")
    save_path = output.joinpath(f"{name}.all.xlsx")
    all_df.write_excel(save_path)


async def entry(output: Path, name: str):
    output.mkdir(parents=True, exist_ok=True)
    await fetch(output, name)
    concat(output, name)


def main(output: Path, name: str):
    asyncio.run(entry(output, name))
