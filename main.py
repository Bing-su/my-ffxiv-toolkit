import argparse
import json
from pathlib import Path

from scrapper import FFXIVDataScrapper


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-j", "--json", default="default.json", help="스크랩 정보를 담은 json파일의 경로"
    )
    parser.add_argument("-p", "--path", default="./data", help="결과 파일 저장 경로")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    with open(args.json) as file:
        info = json.load(file)

    Path(args.path).mkdir(parents=True, exist_ok=True)

    scrapper = FFXIVDataScrapper(info, args.path)
    scrapper.scrap()
