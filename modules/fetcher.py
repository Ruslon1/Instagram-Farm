from TikTokApi import TikTokApi
import os
from modules.database import get_existing_video_links_for_theme, record_video
import asyncio
from concurrent.futures import ThreadPoolExecutor

ms_tokens = os.environ.get("MS_TOKENS", "").split(",")


async def fetch_videos_for_hashtag(hashtag, count=5):
    video_urls = []
    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=ms_tokens, num_sessions=1, sleep_after=3, headless=False)
        tag = api.hashtag(name=hashtag)

        async for video in tag.videos(count=count):
            video_urls.append("https://www.tiktok.com/@/video/" + video.id)

    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        existing_links = await loop.run_in_executor(
            pool, get_existing_video_links_for_theme, hashtag
        )

    new_videos = [url for url in video_urls if url not in existing_links]

    # Add new videos to database
    for url in new_videos:
        record_video(url, hashtag)

    return new_videos