import os
from instagrapi import Client
from modules.logger import telegram_notify

def upload_video_to_instagram(username, password, video_path, caption, token, chat_id):
    try:
        cl = Client()
        cl.login(username, password)
        cl.video_upload(video_path, caption)
        telegram_notify(token, chat_id, f"Successfully uploaded video: {video_path} to account: {username}")
        return True
    except Exception as e:
        print(f"Error uploading video for account {username}: {e}")
        telegram_notify(token, chat_id, f"Error uploading video for account {username}: {e}")
        return False
