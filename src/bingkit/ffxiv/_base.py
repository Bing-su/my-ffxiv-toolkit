import asyncio
import io

import httpr
import polars as pl

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

SHEETS: dict[str, list[str]] = {
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


async def get_csv(
    url: str,
    columns: list[str] | None = None,
):
    async with httpr.AsyncClient() as client:
        resp = await client.get(url)
    if resp.status_code != 200:
        raise ValueError(f"Failed to fetch CSV from {url}: {resp.status_code}")
    content = resp.text
    if content.startswith("#"):
        skip_rows = 0
        skip_rows_after_header = 0
    else:
        skip_rows = 1
        skip_rows_after_header = 1

    return await asyncio.to_thread(
        pl.read_csv,
        io.StringIO(content),
        columns=columns,
        skip_rows=skip_rows,
        skip_rows_after_header=skip_rows_after_header,
        infer_schema_length=30000,
    )
