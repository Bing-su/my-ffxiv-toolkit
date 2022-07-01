import argparse
import re

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--npc", action="store_true")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()
    if args.npc:
        data = pd.read_excel("data/BNpcName.xlsx")
        col_en = "Singular_en"
        col_ko = "Singular_ko"
    else:
        data = pd.read_excel("data/Action.xlsx")
        col_en = "Name_en"
        col_ko = "Name_ko"

    inputs = open("input.txt", encoding="utf-8")
    outputs = open("output.txt", "w", encoding="utf-8")

    pattern = re.compile(r"'(?P<en>.*?)': '.*',")

    for line in inputs:
        if m := pattern.search(line):
            en_skill_name_raw = m.group("en")
            en_skill_name = en_skill_name_raw.replace("\\'", "'")
            match_skills = data[
                (data[col_en] == en_skill_name) & (data[col_ko].notna())
            ]

            if len(match_skills) == 0:
                outputs.write(line)
                continue

            ko_skill_name = match_skills.iloc[-1][col_ko]
            row = f"  '{en_skill_name_raw}': '{ko_skill_name}',\n"
            outputs.write(row)
        else:
            outputs.write(line)

    inputs.close()
    outputs.close()
