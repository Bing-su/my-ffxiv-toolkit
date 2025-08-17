import re
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict, cast

import httpx
import json5
import pandas as pd

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


class RaidbossDataDict(TypedDict):
    en: ParsedData
    de: ParsedData
    fr: ParsedData
    ja: ParsedData


def fetch(url: str) -> RaidbossData:
    ts_url = Path(url).with_suffix(".ts").as_posix().replace("https:/", "https://")
    txt_url = Path(url).with_suffix(".txt").as_posix().replace("https:/", "https://")

    ts_data = httpx.get(ts_url).raise_for_status().text
    txt_data = httpx.get(txt_url).raise_for_status().text
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
            bnpcname.add(obj["source"])

    for line in data.txt.splitlines():
        if not re.match(r"^\d", line):
            continue
        m1 = quoted.search(line)
        if m1:
            s = pp_action(m1.group(1))
            action.update(s)
        m2 = ts_object.search(line)
        if m2:
            try:
                obj = json5.loads(m2.group())
            except json5.JSON5DecodeError:
                continue
            if "source" in obj:
                bnpcname.add(obj["source"])

    return ParsedData(action=sorted(action), bnpcname=sorted(bnpcname))


def to_i18n_data(data: ParsedData) -> RaidbossDataDict:
    actions = pd.read_excel("coinach/Action.all.xlsx")
    b_npc_names = pd.read_excel("coinach/BNpcName.all.xlsx")

    result = {"en": data}

    for i, lang in enumerate(["de", "fr", "ja"]):
        action = []
        bnpcname = []
        df = actions.iloc[:, [0, i + 1]]
        for act in data.action:
            row = df[df.iloc[:, 0].str.lower() == act.lower()]
            action.append(row.iloc[-1, 1])

        df = b_npc_names.iloc[:, [0, i + 1]]
        for bnpc in data.bnpcname:
            row = df[df.iloc[:, 0].str.lower() == bnpc.lower()]
            bnpcname.append(row.iloc[-1, 1])
        result[lang] = ParsedData(action=action, bnpcname=bnpcname)

    return cast(RaidbossDataDict, result)


def to_ts(data: RaidbossDataDict) -> list[str]:
    r = []
    en = data["en"]
    for lang in ["de", "fr", "ja"]:
        d = data[lang]
        r.append("    {")
        r.append(f"      'locale': '{lang}',")
        r.append("      'missingTranslations': true,")
        r.append("      'replaceSync': {")
        for i in range(len(d.bnpcname)):
            key = en.bnpcname[i].replace("'", "\\'")
            value = d.bnpcname[i].replace("'", "\\'")
            r.append(f"        '{key}': '{value}',")
        r.append("      },")
        r.append("      'replaceText': {")
        for i in range(len(d.action)):
            key = en.action[i].replace("'", "\\'")
            value = d.action[i].replace("'", "\\'")
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
