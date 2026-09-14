import asyncio
from pathlib import Path
from typing import Annotated, Literal

from cyclopts import App, Parameter
from upath import UPath

from bingkit.ffxiv.coinach import coinach as _coinach
from bingkit.ffxiv.fflogs import get_all_fight_events as _get_all_fight_events
from bingkit.ffxiv.raidboss import raidboss as _raidboss
from bingkit.ffxiv.rsv import parse_log as _parse_log
from bingkit.ffxiv.rsv import replace as _replace
from bingkit.ffxiv.scrap import scrap as _scrap

app = App(help_on_error=True)


@app.command
def rsv(
    files: Annotated[list[str], Parameter(help="분석할 log 파일 목록")],
    save_path: Annotated[
        str | None,
        Parameter(
            ["-s", "--save-path"],
            help="결과를 저장할 파일 이름",
            show_default=lambda _: "rsv.json",
        ),
    ] = None,
):
    _parse_log(files, save_path)


@app.command()
def scrap(
    config_path: Annotated[
        str | None,
        Parameter(["-c", "--config-path"], help="다운로드 설정 json 파일 경로"),
    ] = None,
    save_dir: Annotated[
        str | None,
        Parameter(
            ["-d", "--save-dir"],
            help="파일들을 저장할 폴더",
            show_default=lambda _: "data",
        ),
    ] = None,
):
    asyncio.run(_scrap(config_path, save_dir))


@app.command()
def replace(
    data_dir: Annotated[
        str | None,
        Parameter(
            ["-d", "--data-dir"],
            help="데이터 파일을 담은 폴더 경로",
            show_default=lambda _: "data",
        ),
    ] = None,
    rsv_path: Annotated[
        str | None,
        Parameter(
            ["-r", "--rsv-path"],
            help="RSV 정보를 담은 json 파일",
            show_default=lambda _: "rsv.json",
        ),
    ] = None,
):
    asyncio.run(_replace(data_dir, rsv_path))


@app.command()
def coinach(
    name: Annotated[str, Parameter(help="가져올 EXD 이름")],
    output: Annotated[
        Path, Parameter(["-o", "--output"], help="결과를 저장할 폴더 경로")
    ] = Path("coinach"),
):
    _coinach(output, name)


@app.command()
def raidboss(
    url: Annotated[str, Parameter(help="파싱할 Cactbot raw content URL")],
    output: Annotated[
        str | None,
        Parameter(
            ["-o", "--output"],
            help="결과를 저장할 파일 이름, - 일 경우 표준 출력, None일 경우 현재 경로에 입력 파일 이름으로 저장",
        ),
    ] = None,
):
    result = _raidboss(url)
    if output == "-":
        print(result)
    elif not output:
        filename = UPath(url).name
        UPath(filename).write_text(result, encoding="utf-8")
    else:
        UPath(output).write_text(result, encoding="utf-8")


@app.command()
def fflogs(
    report_code: Annotated[str, Parameter(help="FFLogs report code")],
    fight_id: Annotated[int, Parameter(help="Fight ID within the report")],
    api_key: Annotated[
        str | None,
        Parameter(
            ["-k", "--api-key"],
            env_var="FFLOGS_API_KEY",
            help="FFLogs API key",
        ),
    ] = None,
    output: Annotated[
        Path | None,
        Parameter(
            ["-o", "--output"],
            help="결과를 저장할 파일 이름, None일 경우 현재 경로에 {report_code}_{fight_id}.{format} 형태로 저장",
        ),
    ] = None,
    format_: Annotated[
        Literal["json", "ndjson", "parquet"],
        Parameter(
            ["-f", "--format"],
            help="출력 파일 형식",
            show_default=True,
        ),
    ] = "json",
):
    import polars as pl

    events = _get_all_fight_events(report_code, fight_id, api_key)
    df = pl.DataFrame(events)
    # Polars에서 UPath 지원 안됨
    output = output or Path(f"{report_code}_{fight_id}.{format_}")
    match format_:
        case "json":
            df.write_json(output)
        case "ndjson":
            df.write_ndjson(output)
        case "parquet":
            df.write_parquet(output)
        case _:
            msg = f"Unsupported format: {format_}"
            raise ValueError(msg)


if __name__ == "__main__":
    app()
