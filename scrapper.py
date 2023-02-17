from __future__ import annotations

from functools import partial
from typing import Literal

import pandas as pd
from mpire import WorkerPool


class FFXIVDataScrapper:
    KO_BASE_URL = (
        "https://raw.githubusercontent.com/Ra-Workspace/ffxiv-datamining-ko/master/csv"
    )
    EN_BASE_URL = "https://raw.githubusercontent.com/xivapi/ffxiv-datamining/master/csv"

    def __init__(self, info: dict[str, list[str]], save_dir: str = "./data") -> None:
        self.info = info
        self.names = tuple(self.info.keys())
        self.save_dir = save_dir

    def url_to_df(self, name: str, lang: Literal["en", "ko"]) -> pd.DataFrame:
        base_url = self.KO_BASE_URL if lang == "ko" else self.EN_BASE_URL
        url = f"{base_url}/{name}.csv"
        columns = ["#"] + self.info[name]
        df = pd.read_csv(
            url, usecols=columns, skiprows=[0, 2], index_col=0, low_memory=False
        )

        rename = {col: f"{col}_{lang}" for col in self.info[name]}
        df.rename(columns=rename, inplace=True)
        return df

    def make_concat_df(self, name: str) -> pd.DataFrame:
        dfs = [self.url_to_df(name, lang) for lang in ("en", "ko")]
        cat_df = pd.concat(dfs, axis=1)
        return cat_df

    def scrap(self, save_dir: str | None = None) -> None:
        if save_dir is None:
            save_dir = self.save_dir

        save_func = partial(self.save, save_dir=save_dir)
        with WorkerPool() as pool:
            dfs = tuple(pool.map(self.make_concat_df, self.names, progress_bar=True))
            pool.map(save_func, zip(dfs, self.names), len(dfs), progress_bar=True)

    def save(self, df: pd.DataFrame, name: str, save_dir: str | None = None) -> None:
        if save_dir is None:
            save_dir = self.save_dir
        path = f"{save_dir}/{name}.xlsx"
        df.to_excel(path)
