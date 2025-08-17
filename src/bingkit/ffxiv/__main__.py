import asyncio
from pathlib import Path
from typing import Annotated

from typer import Argument, Option, Typer

from bingkit.ffxiv.coinach import coinach as _coinach
from bingkit.ffxiv.raidboss import raidboss as _raidboss
from bingkit.ffxiv.rsv import parse_log as _parse_log
from bingkit.ffxiv.rsv import replace as _replace
from bingkit.ffxiv.scrap import scrap as _scrap

app = Typer(no_args_is_help=True)


@app.command(no_args_is_help=True)
def rsv(
    files: Annotated[list[str], Argument(help="분석할 log 파일 목록")],
    save_path: Annotated[
        str | None, Option("-s", "--save-path", help="결과를 저장할 파일 이름")
    ] = None,
):
    _parse_log(files, save_path)


@app.command()
def scrap(
    config_path: Annotated[
        str | None,
        Option("-c", "--config-path", help="다운로드 설정 json 파일 경로"),
    ] = None,
    save_dir: Annotated[
        str | None, Option("-d", "--save-dir", help="파일들을 저장할 폴더")
    ] = None,
):
    asyncio.run(_scrap(config_path, save_dir))


@app.command()
def replace(
    data_dir: Annotated[
        str | None, Option("-d", "--data-dir", help="데이터 파일을 담은 폴더 경로")
    ] = None,
    rsv_path: Annotated[
        str | None, Option("-r", "--rsv-path", help="RSV 정보를 담은 json 파일")
    ] = None,
):
    asyncio.run(_replace(data_dir, rsv_path))


@app.command()
def coinach(
    name: Annotated[str, Argument(help="가져올 EXD 이름")],
    output: Annotated[
        Path, Option("-o", "--output", help="결과를 저장할 폴더 경로")
    ] = Path("coinach"),
):
    _coinach(output, name)


@app.command()
def raidboss(
    url: Annotated[str, Argument(help="파싱할 Cactbot raw content URL")],
):
    result = _raidboss(url)
    print(result)


if __name__ == "__main__":
    app()
