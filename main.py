from modules.database import load_accounts_and_videos
from modules.tasks import process_video

import os
import time

def main():
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    accounts, account_to_videos = load_accounts_and_videos()

    print(accounts)
    print(account_to_videos)

    for account in accounts:
        username, password, theme = account
        videos = account_to_videos.get(theme, [])
        process_video.delay(account, videos, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)


if __name__ == "__main__":
    os.makedirs("./videos", exist_ok=True)
    time.sleep(1)
    main()
