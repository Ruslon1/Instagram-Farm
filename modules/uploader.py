
from pathlib import Path
from instagrapi import Client
from instagrapi.exceptions import LoginRequired
from modules.logger import telegram_notify
import time
import random

SESSION_DIR = Path("./sessions")
SESSION_DIR.mkdir(exist_ok=True)

def get_session_path(username: str) -> Path:
    return SESSION_DIR / f"{username}.session"

def upload_video_to_instagram(username: str, password: str, video_path: str,
                              caption: str, token: str, chat_id: str) -> bool:
    try:
        cl = Client()
        session_path = get_session_path(username)

        # Try to load existing session
        if session_path.exists():
            try:
                cl.load_settings(session_path)
                # Test if session is still valid
                cl.get_timeline_feed()
            except (LoginRequired, Exception) as e:
                print(f"Session expired for {username}, relogging in...")
                # Add random delay to mimic human behavior
                time.sleep(random.uniform(2, 5))
                cl.login(username, password)
                cl.dump_settings(session_path)
        else:
            time.sleep(random.uniform(2, 5))  # Initial login delay
            cl.login(username, password)
            cl.dump_settings(session_path)

        # Add delay before upload
        time.sleep(random.uniform(5, 15))

        # Upload video (convert video_path to Path if needed)
        cl.video_upload(video_path, caption)
        telegram_notify(token, chat_id,
                        f"Successfully uploaded video: {video_path} to account: {username}")
        return True

    except Exception as e:
        print(f"Error uploading video for account {username}: {e}")
        telegram_notify(token, chat_id,f"Error uploading video for account {username}: {e}")

        if "login" in str(e).lower():
            try:
                session_path.unlink(missing_ok=True)
            except Exception as e:
                print(f"Error removing session file: {e}")

        return False