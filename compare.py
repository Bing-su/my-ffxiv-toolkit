import argparse
import re

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--npc", action="store_true")
    parser.add_argument("-p", "--place", action="store_true")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()
    if args.npc:
        data = pd.read_excel("data/BNpcName.xlsx")
        col_en = "Singular_en"
        col_ko = "Singular_ko"
    elif args.place:
        data = pd.read_excel("data/PlaceName.xlsx")
        col_en = "Name_en"
        col_ko = "Name_ko"
    else:
        data = pd.read_excel("data/Action.xlsx")
        col_en = "Name_en"
        col_ko = "Name_ko"

    inputs = open("input.txt", encoding="utf-8")
    outputs = open("output.txt", "w", encoding="utf-8")

    pattern = re.compile(r"'(?P<en>.*?)': '.*',")

    for line in inputs:
        if m := pattern.search(line):
            en_name_raw = m.group("en")
            en_name = en_name_raw.replace("\\'", "'")
            lower_data = data[col_en].str.lower()
            match_skills = data[
                (lower_data == en_name.lower()) & (data[col_ko].notna())
            ]

            if len(match_skills) == 0:
                outputs.write(line)
                continue

            ko_name = match_skills.iloc[-1][col_ko]
            row = f"    '{en_name_raw}': '{ko_name}',\n"
            outputs.write(row)
        else:
            outputs.write(line)

    inputs.close()
    outputs.close()
