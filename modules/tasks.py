from celery_app import app
from modules.downloader import get_download_link, download_video
from modules.uploader import upload_video_to_instagram
from modules.logger import telegram_notify
from modules.database import record_publication
import os
import random
import time

@app.task
def process_video(account, video, telegram_token, chat_id):
    username, password, purpose = account
    video_purpose, link = video

    if video_purpose != purpose:
        return

    download_url = get_download_link(link)
    if not download_url:
        telegram_notify(telegram_token, chat_id, f"Failed to download video from: {link}")
        return

    output_path = f"./videos/{username}_{random.randint(1, 1000)}.mp4"
    success = download_video(download_url, output_path)
    if not success:
        telegram_notify(telegram_token, chat_id, f"Failed to download video from: {link}")
        return

    caption = f"Purpose: {purpose} #automatedupload"
    upload_result = upload_video_to_instagram(username, password, output_path, caption, telegram_token, chat_id)
    if upload_result:
        telegram_notify(telegram_token, chat_id, f"Successfully uploaded video from: {link} to account: {username}")
        record_publication(username, link)
        os.remove(output_path)
    else:
        telegram_notify(telegram_token, chat_id, f"Failed to upload video from: {link} to account: {username}")

    time.sleep(random.randint(300, 1500))
