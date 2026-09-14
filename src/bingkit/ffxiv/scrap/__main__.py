import asyncio

from .scrapper import scrap


def cli():
    asyncio.run(scrap())


if __name__ == "__main__":
    import cyclopts

    cyclopts.run(cli)
