from TikTokApi import TikTokApi
import os
import asyncio
import time
import random
from concurrent.futures import ThreadPoolExecutor
from modules.database import get_existing_video_links_for_theme, record_video
from dataclasses import dataclass
from typing import List, Optional

ms_tokens = os.environ.get("MS_TOKENS", "").split(",") if os.environ.get("MS_TOKENS") else []


@dataclass
class VideoInfo:
    url: str
    title: str
    author: str
    created_at: int
    views: int = 0
    likes: int = 0


class FanAccountFetcher:
    def __init__(self):
        self.api = None

    async def initialize_api(self):
        """Initialize TikTok API with anti-detection settings"""
        if self.api:
            return
        try:
            self.api = TikTokApi()
            await self.api.create_sessions(
                ms_tokens=ms_tokens,
                num_sessions=1,
                headless=False,
                sleep_after=random.randint(5, 10),
                browser='chromium'
            )
            print("✅ TikTok API initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize TikTok API: {e}")
            raise

    async def fetch_videos_from_account(self, username: str, theme: str, count: int = 20) -> List[str]:
        """Fetch latest videos from a specific TikTok account"""
        await self.initialize_api()
        print(f"🔍 Fetching {count} videos from @{username} for theme '{theme}'")

        try:
            delay = random.uniform(2, 5)
            print(f"⏳ Waiting {delay:.1f} seconds...")
            await asyncio.sleep(delay)

            user = self.api.user(username=username)
            videos = []
            video_count = 0

            async for video in user.videos(count=count):
                if video_count >= count:
                    break

                # Extract video data safely
                video_id = getattr(video, 'id', '')
                video_desc = getattr(video, 'desc', '') or ''
                create_time = getattr(video, 'createTime', int(time.time()))

                # Get stats safely
                stats = getattr(video, 'stats', {}) or {}
                views = stats.get('playCount', 0) if stats else 0
                likes = stats.get('diggCount', 0) if stats else 0

                # Fix: Ensure views is an integer, not None
                views = views or 0
                likes = likes or 0

                # Get author username safely
                author_username = username
                if hasattr(video, 'author') and video.author:
                    author_username = (getattr(video.author, 'username', username) or
                                     getattr(video.author, 'uniqueId', username) or username)

                video_url = f"https://www.tiktok.com/@{author_username}/video/{video_id}"
                video_info = VideoInfo(
                    url=video_url,
                    title=video_desc,
                    author=author_username,
                    created_at=create_time,
                    views=views,
                    likes=likes
                )

                videos.append(video_info)
                video_count += 1

                print(f"  📼 Video {video_count}: {video_desc[:50]}... (👀 {views:} views)")

                if video_count % 5 == 0:
                    await asyncio.sleep(random.uniform(0.5, 1.5))

            print(f"✅ Successfully fetched {len(videos)} videos from @{username}")

            # Filter new videos
            #loop = asyncio.get_running_loop()
            #with ThreadPoolExecutor() as pool:
            #    existing_links = await loop.run_in_executor(
            #        pool, get_existing_video_links_for_theme, theme
            #    )

            new_videos = []
            existing_links = []
            for video in videos:
                if video.url not in existing_links:
                    new_videos.append(video.url)
                    #record_video(video.url, theme)

            print(f"🆕 Found {len(new_videos)} new videos for theme '{theme}'")
            return new_videos

        except Exception as e:
            print(f"❌ Error fetching videos from @{username}: {e}")
            return []

    async def close(self):
        """Close TikTok API sessions"""
        if self.api:
            await self.api.close_sessions()
            print("🔒 TikTok API sessions closed")


async def fetch_videos_for_hashtag(hashtag, count=5):
    """Legacy function - kept for backward compatibility"""
    print(f"⚠️  Legacy function called with hashtag '{hashtag}' - should use account-based fetching")
    return []


async def fetch_videos_for_theme_from_accounts(theme: str, fan_accounts: List[str], videos_per_account: int = 10) -> List[str]:
    """
    Fetch videos from multiple fan accounts for a specific theme

    Args:
        theme: Theme name (e.g., 'ishowspeed')
        fan_accounts: List of TikTok usernames
        videos_per_account: How many latest videos to fetch from each account

    Returns:
        List of new video URLs
    """
    fetcher = FanAccountFetcher()
    all_new_videos = []

    try:
        for account in fan_accounts:
            try:
                print(f"\n🎯 Processing account @{account} for theme '{theme}'")

                new_videos = await fetcher.fetch_videos_from_account(
                    username=account,
                    theme=theme,
                    count=videos_per_account
                )

                all_new_videos.extend(new_videos)

                if account != fan_accounts[-1]:
                    delay = random.uniform(3, 8)
                    print(f"⏳ Waiting {delay:.1f} seconds before next account...")
                    await asyncio.sleep(delay)

            except Exception as e:
                print(f"❌ Error processing account @{account}: {e}")
                continue

        print(f"\n🎉 Total new videos found: {len(all_new_videos)}")
        return all_new_videos

    except Exception as e:
        print(f"❌ Error in theme fetching: {e}")
        return []
    finally:
        await fetcher.close()


if __name__ == "__main__":
    async def test():
        theme = "ishowspeed"
        fan_accounts = ["ishowdailyupdate3"]

        print(f"🧪 Testing fetcher for theme '{theme}'")
        videos = await fetch_videos_for_theme_from_accounts(theme, fan_accounts, 5)

        print(f"\n📊 Results:")
        print(f"Found {len(videos)} new videos:")
        for i, url in enumerate(videos, 1):
            print(f"  {i}. {url}")

    asyncio.run(test())