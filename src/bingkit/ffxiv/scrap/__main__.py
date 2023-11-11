import asyncio
import platform

from .scrapper import scrap


def cli():
    asyncio.run(scrap())


if __name__ == "__main__":
    import typer

    if platform.system() == "Windows":
        import winloop

        winloop.install()

    typer.run(cli)
