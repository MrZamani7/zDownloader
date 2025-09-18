import asyncio
import httpx
import logging

async def downloader(link):
    client = httpx.AsyncClient()
    try:
        async with client.stream("GET", link) as resp:
            print(resp)
    except Exception as e:
        print(e)

async def async_main():
    link = input("Enter the link to begin download: ")
    await downloader(link)

if __name__ == "__main__":
    asyncio.run(async_main())