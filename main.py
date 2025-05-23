from modules.database import load_accounts_and_videos
from modules.tasks import process_video

import os

def main():
    print("START")
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    accounts, account_to_videos = load_accounts_and_videos()
    
    for account in accounts:
        username, password, theme = account
        videos = account_to_videos.get(theme, [])
        for video in videos:
            print("RPOCESS")
            process_video.delay(account, video, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)

if __name__ == "__main__":
    os.makedirs("./videos", exist_ok=True)
    main()
