from TikTokApi import TikTokApi
import os

ms_tokens = os.environ.get("MS_TOKENS", "").split(",")

async def get_hashtag_videos():
    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=ms_tokens, num_sessions=1, sleep_after=3, headless=False)
        tag = api.hashtag(name="караганда")

        async for video in tag.videos(count=2):
            print(video.url)