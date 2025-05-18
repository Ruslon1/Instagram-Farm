import os
import random
import time
from modules.downloader import get_download_link, download_video
from modules.uploader import upload_video_to_instagram

def process_account(account, videos, token, chat_id):
    username, password, purpose = account
    for video in videos:
        video_purpose, link = video
        if video_purpose != purpose:
            continue
        download_url = get_download_link(link)
        if not download_url:
            continue
        output_path = f"./videos/{username}_video.mp4"
        if download_video(download_url, output_path):
            caption = f"Purpose: {purpose} #automatedupload"
            if upload_video_to_instagram(username, password, output_path, caption, token, chat_id):
                os.remove(output_path)
        time.sleep(random.randint(300, 1500))
