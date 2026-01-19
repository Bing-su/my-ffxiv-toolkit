import asyncio
import io
from pathlib import Path

import httpx
import polars as pl
from loguru import logger
from tqdm.asyncio import tqdm

BASE_URL: dict[str, str] = {
    "en": "https://raw.githubusercontent.com/xivapi/ffxiv-datamining/refs/heads/master/csv/en/{name}.csv",
    "de": "https://raw.githubusercontent.com/xivapi/ffxiv-datamining/refs/heads/master/csv/de/{name}.csv",
    "fr": "https://raw.githubusercontent.com/xivapi/ffxiv-datamining/refs/heads/master/csv/fr/{name}.csv",
    "ja": "https://raw.githubusercontent.com/xivapi/ffxiv-datamining/refs/heads/master/csv/ja/{name}.csv",
    "cn": "https://raw.githubusercontent.com/thewakingsands/ffxiv-datamining-cn/refs/heads/master/{name}.csv",
    "ko": "https://raw.githubusercontent.com/Ra-Workspace/ffxiv-datamining-ko/refs/heads/master/csv/{name}.csv",
    "tc": "https://raw.githubusercontent.com/thewakingsands/ffxiv-datamining-tc/refs/heads/main/{name}.csv",
}

LANG = tuple(BASE_URL.keys())

mapping: dict[str, list[str]] = {
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


async def download_csv(client: httpx.AsyncClient, url: str, output: Path):
    resp = await client.get(url)
    resp.raise_for_status()
    content = resp.text
    if content.startswith("#"):
        skip_rows = 0
        skip_rows_after_header = 0
    else:
        skip_rows = 1
        skip_rows_after_header = 1

    df = await asyncio.to_thread(
        pl.read_csv,
        io.StringIO(content),
        skip_rows=skip_rows,
        skip_rows_after_header=skip_rows_after_header,
        infer_schema_length=30000,
    )
    df.write_csv(output)
    logger.info(f"csv saved at {output}")


async def fetch(output: Path, name: str):
    total = len(LANG)
    pbar = tqdm(total=total)

    async with httpx.AsyncClient() as client:
        async with asyncio.TaskGroup() as tg:
            for lang, baseurl in BASE_URL.items():
                url = baseurl.format(name=name)
                name_with_lang = f"{name}.{lang}.csv"
                file_path = output.joinpath(name_with_lang)
                fut = download_csv(client, url, file_path)
                tg.create_task(fut).add_done_callback(lambda _: pbar.update())

    pbar.close()


def concat(output: Path, name: str):
    csv_files = list(output.glob(f"{name}*.csv"))
    csv_files.sort(key=lambda x: LANG.index(x.stem.split(".")[-1]))
    use_cols = mapping[name]
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
