import asyncio
import platform

from .scrapper import scrap


def cli():
    asyncio.run(scrap())


if __name__ == "__main__":
    import cyclopts

    if platform.system() == "Windows":
        import winloop

        winloop.install()

    cyclopts.run(cli)
