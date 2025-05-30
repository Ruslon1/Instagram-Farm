from modules.database import load_accounts_and_videos
from modules.tasks import process_video
from modules.fetcher import fetch_videos_for_hashtag
from celery_app import app

import os
import time
import asyncio


def main():
    app.control.purge()
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    accounts, _, _ = load_accounts_and_videos()
    themes = {theme for _, _, theme, _ in accounts}

    #for theme in themes:
        #asyncio.run(fetch_videos_for_hashtag(theme, 30))

    accounts, account_to_videos, published_set = load_accounts_and_videos()
    for account in accounts:
        username, password, theme, two_fa_key = account
        videos = account_to_videos.get(theme, [])

        unpublished_videos = [
            video for video in videos
            if (username, video) not in published_set
        ]
        process_video.delay((username, password, theme, two_fa_key), unpublished_videos, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)


if __name__ == "__main__":
    os.makedirs("./videos", exist_ok=True)
    time.sleep(1)
    main()