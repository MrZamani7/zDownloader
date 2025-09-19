import asyncio
import aiohttp
import aiofiles
from aiofiles import os as aos
import logging
import os

async def delete_file(name: str, dir: str|None) -> None:
    file_path = os.path.join(dir, name) if dir else name
    if os.path.exists(file_path):
        await aos.remove(file_path)

async def merge_files(name: str, dir: str|None, temp_dir: str, part_numbers: list[int]) -> None:
    file_path = os.path.join(dir, name) if dir else name
    async with aiofiles.open(file_path, "wb") as afw:
        for part_number in part_numbers:
            part = os.path.join(temp_dir, name + f"part{part_number}")

async def calc_chunks(length: int, number: int) -> list[str]:
    chunk_size = int(length / number)
    chunk_range: list[str] = []
    for n in range(number):
        chunk_range.append(f"{(n*chunk_size)+n}-{((n+1)*chunk_size)+n}")
    return chunk_range

async def party(url: str, range: str, part_number: int, temp_dir: str) -> int:
    headers = {"Range" : f"bytes={range}"}
    file_name = url.split('/')[-1]
    file_path = os.path.join(temp_dir, file_name + f"part{part_number}")
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as resp:
            async with aiofiles.open(file_path, "wb") as file:
                while (True):
                    file_chunk = await resp.content.read(10 * 1024 * 1024)
                    if not file_chunk:
                        break
                    await file.write(file_chunk)
    return part_number

async def downloader(url: str) -> None:
    async with aiohttp.ClientSession() as session:
        async with session.head(url) as headers:
            if headers.content_length:
                chunk_range = await calc_chunks(headers.content_length, 6)
                async with aiofiles.tempfile.TemporaryDirectory() as temp_dir:
                    download_future = asyncio.gather(
                        *[
                            party(url, range, part_number, temp_dir) for part_number, range in enumerate(chunk_range)
                        ]
                    )
                    print("Download started..")
                    downloaded = False
                    saved = False
                    try:
                        await download_future
                        downloaded = True
                    except Exception as e:
                        print(e)
                        downloaded = False
                    if downloaded:
                        print("Downloaded")
                    else:
                        print("Error")
            else:
                print("This link has no length header!")

async def main() -> None:
    #link = input("Enter the link to begin download: ")
    link = "https://www.kasandbox.org/programming-images/avatars/leaf-red.png"
    await downloader(link)

if __name__ == "__main__":
    asyncio.run(main())