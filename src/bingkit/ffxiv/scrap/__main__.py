import asyncio
import platform

from .scrapper import scrap

if __name__ == "__main__":
    if platform.system() == "Windows":
        import winloop

        winloop.install()

    asyncio.run(scrap())
