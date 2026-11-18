import asyncio
import pygame  # noqa: F401  (listed here so the web build bundles pygame)

from brady.ui import App


async def main():
    await App().run()


if __name__ == "__main__":
    asyncio.run(main())
