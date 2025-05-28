from modules.database import load_accounts_and_videos
from modules.tasks import process_video
from modules.fetcher import fetch_videos_for_hashtag

import os
import time
import asyncio


def main():
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    accounts, account_to_videos, published_set = load_accounts_and_videos()

    themes = {theme for _, _, theme in accounts}

    for theme in themes:
        asyncio.run(fetch_videos_for_hashtag(theme, 30))

    for account in accounts:
        username, password, theme = account
        videos = account_to_videos.get(theme, [])

        unpublished_videos = [
            video for video in videos
            if (username, video) not in published_set
        ]

        process_video.delay(account, unpublished_videos, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)


if __name__ == "__main__":
    os.makedirs("./videos", exist_ok=True)
    time.sleep(1)
    main()
