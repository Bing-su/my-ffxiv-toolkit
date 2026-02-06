import re
from dataclasses import dataclass
from typing import TypedDict, cast

import json5
import polars as pl
from upath import UPath

ts_object = re.compile(r"\{[^}]*\}")
quoted = re.compile(r"\"([^\"]+)\"")


@dataclass
class RaidbossData:
    ts: str
    txt: str


@dataclass
class ParsedData:
    action: list[str]
    bnpcname: list[str]


@dataclass
class PairData:
    action: dict[str, str]
    bnpcname: dict[str, str]


class RaidbossDataDict(TypedDict):
    en: PairData
    de: PairData
    fr: PairData
    ja: PairData
    cn: PairData
    ko: PairData


langs = ["en", "de", "fr", "ja", "cn", "ko"]


def add_to_set(s: set[str], item: str | list[str]) -> set[str]:
    s = s.copy()
    if isinstance(item, list):
        for i in item:
            s.add(i.strip())
    else:
        s.add(item.strip())
    return s


def fetch(url: str) -> RaidbossData:
    ts_url = UPath(url).with_suffix(".ts")
    txt_url = UPath(url).with_suffix(".txt")

    ts_data = ts_url.read_text(encoding="utf-8")
    try:
        txt_data = txt_url.read_text(encoding="utf-8")
    except FileNotFoundError:
        txt_data = ""
    return RaidbossData(ts=ts_data, txt=txt_data)


def pp_action(s: str) -> list[str]:
    if s.startswith("-"):
        return []
    s = re.sub(r"\s+\d+$", "", s)
    s = re.sub(r"\?$", "", s)
    s = re.sub(r"\s*\(.*?\)$", "", s)
    return s.split("/")


def parse(data: RaidbossData) -> ParsedData:
    action = set()
    bnpcname = set()
    for line in data.ts.splitlines():
        m = ts_object.search(line)
        if not m:
            continue
        try:
            obj = json5.loads(m.group())
        except json5.JSON5DecodeError:
            continue
        if "source" in obj:
            bnpcname = add_to_set(bnpcname, obj["source"])
        if "target" in obj:
            bnpcname = add_to_set(bnpcname, obj["target"])

    for line in data.txt.splitlines():
        if not re.match(r"^\d", line):
            continue
        m1 = quoted.search(line)
        if m1:
            s = pp_action(m1.group(1))
            action = add_to_set(action, s)
        m2 = ts_object.search(line)
        if m2:
            try:
                obj = json5.loads(m2.group())
            except json5.JSON5DecodeError:
                continue
            if "source" in obj:
                bnpcname = add_to_set(bnpcname, obj["source"])
            if "target" in obj:
                bnpcname = add_to_set(bnpcname, obj["target"])

    return ParsedData(action=sorted(action), bnpcname=sorted(bnpcname))


def to_i18n_data(data: ParsedData) -> RaidbossDataDict:
    actions: pl.DataFrame = pl.read_excel("coinach/Action.all.xlsx")
    b_npc_names: pl.DataFrame = pl.read_excel("coinach/BNpcName.all.xlsx")

    result = {"en": PairData(action={}, bnpcname={})}
    for act in data.action:
        result["en"].action[act] = act
    for bnpc in data.bnpcname:
        result["en"].bnpcname[bnpc] = bnpc

    for i, lang in enumerate(langs[1:]):
        action: dict[str, str] = {}
        bnpcname: dict[str, str] = {}
        df = actions.select(pl.nth(0, i + 1))
        for act in data.action:
            row = df.filter(pl.nth(0).str.to_lowercase() == act.lower())
            if row.is_empty():
                continue
            action[act] = row.item(-1, 1)

        df = b_npc_names.select(pl.nth(0, i + 1))
        for bnpc in data.bnpcname:
            row = df.filter(pl.nth(0).str.to_lowercase() == bnpc.lower())
            if row.is_empty():
                continue
            bnpcname[bnpc] = row.item(-1, 1)
        result[lang] = PairData(action=action, bnpcname=bnpcname)

    return cast(RaidbossDataDict, result)


def to_ts(data: RaidbossDataDict) -> list[str]:
    r = []
    en = data["en"]
    for lang in langs[1:]:
        d = data[lang]
        r.append("    {")
        r.append(f"      'locale': '{lang}',")
        r.append("      'missingTranslations': true,")
        r.append("      'replaceSync': {")
        for key_raw in sorted(en.bnpcname):
            key = key_raw.replace("'", "\\'")
            if key_raw not in d.bnpcname:
                continue
            value = d.bnpcname[key_raw].replace("'", "\\'")
            r.append(f"        '{key}': '{value}',")
        r.append("      },")
        r.append("      'replaceText': {")
        for key_raw in sorted(en.action):
            key = key_raw.replace("'", "\\'")
            if key_raw not in d.action:
                continue
            value = d.action[key_raw].replace("'", "\\'")
            r.append(f"        '{key}': '{value}',")
        r.append("      },")
        r.append("    },")

    return r


def raidboss(url: str) -> str:
    data = fetch(url)
    parsed = parse(data)
    i18n_all = to_i18n_data(parsed)
    ts_lines = to_ts(i18n_all)
    return "\n".join(ts_lines)
