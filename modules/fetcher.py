from TikTokApi import TikTokApi
import os

ms_tokens = os.environ.get("MS_TOKENS", "").split(",")


async def fetch_videos_for_hashtag(hashtag, count=5):
    video_urls = []
    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=ms_tokens, num_sessions=1, sleep_after=3, headless=False)
        tag = api.hashtag(name=hashtag)

        async for video in tag.videos(count=count):
            video_urls.append(video.url)
    return video_urls
