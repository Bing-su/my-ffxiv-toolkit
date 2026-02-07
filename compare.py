import argparse
import os
import re

import polars as pl
from tqdm.auto import tqdm


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--npc", action="store_true")
    parser.add_argument("-p", "--place", action="store_true")
    parser.add_argument("-a", "--all", action="store_true")
    parser.add_argument("-i", "--input", default="input.txt")
    parser.add_argument("-o", "--output", default="output.txt")
    return parser.parse_args()


def compare(
    action: bool = False,
    npc: bool = False,
    place: bool = False,
    input_file: str = "input.txt",
    output_file: str = "output.txt",
) -> None:
    if not any([action, npc, place]):
        action = True

    if npc:
        data: pl.DataFrame = pl.read_excel("data/BNpcName.xlsx")
        col_en = "Singular_en"
        col_ko = "Singular_ko"
    elif place:
        data: pl.DataFrame = pl.read_excel("data/PlaceName.xlsx")
        col_en = "Name_en"
        col_ko = "Name_ko"
    elif action:
        data: pl.DataFrame = pl.read_excel("data/Action.xlsx")
        col_en = "Name_en"
        col_ko = "Name_ko"
    else:
        raise ValueError

    inputs = open(input_file, encoding="utf-8")
    outputs = open(output_file, "w", encoding="utf-8")

    pattern = re.compile(r"(?P<space> *)'(?P<en>.*?)': '.*',")

    for line in inputs:
        if m := pattern.search(line):
            en_name_raw = m.group("en")
            en_name = en_name_raw.replace("\\'", "'").replace("Pandaemon", "Pandæmon")
            en_name = re.sub(r"\(.*\)", "", en_name)
            match_skills = data.filter(
                (pl.col(col_en).str.to_lowercase() == en_name.lower())
                & pl.col(col_ko).is_not_null()
                & pl.col(col_ko).ne(pl.lit(""))
                & ~pl.col(col_ko).str.starts_with("_rsv_")
            )

            if match_skills.is_empty():
                outputs.write(line)
                continue

            len_space = len(m.group("space"))
            ko_name = match_skills.item(-1, col_ko)
            if "_rsv_" in ko_name:
                ko_name = en_name_raw
            row = " " * len_space + f"'{en_name_raw}': '{ko_name}',\n"
            outputs.write(row)
        else:
            outputs.write(line)

    inputs.close()
    outputs.close()


if __name__ == "__main__":
    args = parse_args()
    if not args.all:
        compare(
            npc=args.npc,
            place=args.place,
            input_file=args.input,
            output_file=args.output,
        )

    else:
        pbar = tqdm(total=3)
        compare(npc=True, input_file=args.input, output_file="output_npc.txt")
        pbar.update()
        compare(place=True, input_file="output_npc.txt", output_file="output_place.txt")
        pbar.update()
        compare(action=True, input_file="output_place.txt", output_file="output.txt")
        pbar.update()

        for file in ["output_place.txt", "output_npc.txt"]:
            os.remove(file)

        pbar.close()

    print("Done!")
