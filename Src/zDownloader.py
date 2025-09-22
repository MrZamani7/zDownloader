import asyncio
import aiohttp
import aiofiles
from aiofiles import os as aos
import os
import logging
import logging.config

log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logging.conf")
logging.config.fileConfig(log_file_path)
logger = logging.getLogger("Logger")

async def delete_file(name: str, dir: str|None) -> None:
    file_path = os.path.join(dir, name) if dir else name
    if os.path.exists(file_path):
        await aos.remove(file_path)
        logger.info(f"File '{name}' removed from '{dir}'") if dir else logger.info(f"File '{name}' removed")

async def merge_files(file_name: str, file_path: str, temp_dir: str, part_numbers: list[int]) -> bool:
    async with aiofiles.open(file_path, "wb") as afw:
        for part_number in part_numbers:
            part_of_file = os.path.join(temp_dir, file_name + f".part{part_number}")
            async with aiofiles.open(part_of_file, "rb") as afr:
                while (True):
                    part_chunk = await afr.read(10 * 1024 * 1024)
                    if not part_chunk:
                        break
                    await afw.write(part_chunk)
            await delete_file(part_of_file, None)
    return True

async def calc_chunks(length: int, number: int) -> list[str]:
    chunk_size = int(length / number)
    chunk_range: list[str] = []
    for n in range(number):
        chunk_range.append(f"{(n*chunk_size)+n}-{((n+1)*chunk_size)+n}")
    return chunk_range

async def party(url: str, range: str, part_number: int, temp_dir: str) -> int:
    headers = {"Range" : f"bytes={range}"}
    file_name = url.split('/')[-1]
    file_path = os.path.join(temp_dir, file_name + f".part{part_number}")
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
                    file_name = url.split('/')[-1]
                    file_dir = None
                    file_path = os.path.join(file_dir, file_name) if file_dir else file_name
                    if downloaded:
                        print("Merging parts..")
                        saved = await merge_files(file_name, file_path, temp_dir, list(range(len(chunk_range))))
                    else:
                        print("Cleaning temp files..")
                        clean_future = asyncio.gather(
                            *[
                                delete_file(file_name + f".part{part_number}", temp_dir) for part_number in range(len(chunk_range))
                            ]
                        )
                        await clean_future
                    if saved:
                        print(f"File downloaded in {file_path}")
                    else:
                        print(f"Cannot download file from {url}")
            else:
                print("This link has no length header!")

async def main() -> None:
    link = input("Enter the link to begin download: ")
    await downloader(link)

if __name__ == "__main__":
    asyncio.run(main())