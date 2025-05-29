
from pathlib import Path
from instagrapi import Client
from instagrapi.exceptions import LoginRequired
from modules.logger import telegram_notify
import time
import random
import requests

SESSION_DIR = Path("./sessions")
SESSION_DIR.mkdir(exist_ok=True)

def get_session_path(username: str) -> Path:
    return SESSION_DIR / f"{username}.session"

def upload_video_to_instagram(username: str, password: str, video_path: str, caption: str, token: str, chat_id: str, two_fa_key: str = None) -> bool:
    try:
        cl = Client()
        session_path = get_session_path(username)

        if session_path.exists():
            try:
                cl.load_settings(session_path)
                cl.get_timeline_feed()
            except (LoginRequired, Exception) as e:
                print(f"Session expired for {username}, relogging in...")
                time.sleep(random.uniform(2, 5))
                if two_fa_key:
                    response = requests.get(f"https://2fa.fb.rip/api/otp/{two_fa_key}").json()
                    if response.get("ok"):
                        fa_code = response["data"]["otp"]
                        cl.login(username, password, verification_code=fa_code)
                    else:
                        raise Exception(f"Failed to get 2FA code: {response}")
                else:
                    cl.login(username, password)
                cl.dump_settings(session_path)
        else:
            time.sleep(random.uniform(2, 5))
            if two_fa_key:
                response = requests.get(f"https://2fa.fb.rip/api/otp/{two_fa_key}").json()
                if response.get("ok"):
                    fa_code = response["data"]["otp"]
                    cl.login(username, password, verification_code=fa_code)
                else:
                    raise Exception(f"Failed to get 2FA code: {response}")
            else:
                cl.login(username, password)
            cl.dump_settings(session_path)

        time.sleep(random.uniform(5, 15))
        cl.video_upload(video_path, caption)
        telegram_notify(token, chat_id, f"Successfully uploaded video: {video_path} to account: {username}")
        return True

    except Exception as e:
        print(f"Error uploading video for account {username}: {e}")
        telegram_notify(token, chat_id, f"Error uploading video for account {username}: {e}")

        if "login" in str(e).lower():
            try:
                session_path.unlink(missing_ok=True)
            except Exception as e:
                print(f"Error removing session file: {e}")

        return False