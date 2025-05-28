from celery_app import app
from modules.downloader import get_download_link, download_video
from modules.uploader import upload_video_to_instagram
from modules.logger import telegram_notify
from modules.database import record_publication, is_video_published
import os
import random
import time
import hashlib


@app.task
def process_video(account, videos, telegram_token, chat_id):
    username, password, purpose = account

    for video in videos:
        if is_video_published(username, video):
            continue

        download_url = get_download_link(video)
        if not download_url:
            telegram_notify(telegram_token, chat_id, f"Failed to download video from: {video}")
            continue

        unique_hash = hashlib.md5(f"{username}_{video}".encode()).hexdigest()
        output_path = f"./videos/{unique_hash}.mp4"
        success = download_video(download_url, output_path)
        if not success:
            telegram_notify(telegram_token, chat_id, f"Failed to download video from: {video}")
            continue

        caption = f""
        upload_result = upload_video_to_instagram(username, password, output_path, caption, telegram_token, chat_id)
        if upload_result:
            telegram_notify(telegram_token, chat_id, f"Successfully uploaded video from: {video} to account: {username}")
            record_publication(username, video)
            os.remove(output_path)
        else:
            telegram_notify(telegram_token, chat_id, f"Failed to upload video from: {video} to account: {username}")

        time.sleep(random.randint(300, 1500))