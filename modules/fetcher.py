from TikTokApi import TikTokApi
import asyncio
import os

ms_token = os.environ.get("MS_TOKEN")

async def get_hashtag_videos():
    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=3)
        tag = api.hashtag(name="gym")
        async for video in tag.videos(count=30):
            print(video)
            print(video.as_dict)


if __name__ == "__main__":
    asyncio.run(get_hashtag_videos())
