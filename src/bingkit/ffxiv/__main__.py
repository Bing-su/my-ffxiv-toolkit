import asyncio
from typing import Optional

from typer import Argument, Option, Typer
from typing_extensions import Annotated

from bingkit.ffxiv.rsv import parse_log as _parse_log
from bingkit.ffxiv.scrap import scrap as _scrap

app = Typer(no_args_is_help=True)


@app.command(no_args_is_help=True)
def rsv(
    files: Annotated[list[str], Argument(help="분석할 log 파일 목록")],
    save_path: Annotated[
        Optional[str], Option("-s", "--save-path", help="결과를 저장할 파일 이름")
    ] = None,
):
    _parse_log(files, save_path)


@app.command(no_args_is_help=True)
def scrap(
    config_path: Annotated[
        Optional[str], Option("-c", "--config-path", help="다운로드 설정 json 파일 경로")
    ] = None,
    save_dir: Annotated[
        Optional[str], Option("-d", "--save-dir", help="파일들을 저장할 폴더")
    ] = None,
):
    asyncio.run(_scrap(config_path, save_dir))


if __name__ == "__main__":
    app()
