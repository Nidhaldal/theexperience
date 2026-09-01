import asyncio

from app.services.lastfm import get_album_popularity


async def main():
    result = await get_album_popularity(
        "The Rolling Stones",
        "Let It Bleed",
    )

    print(result)


asyncio.run(main())