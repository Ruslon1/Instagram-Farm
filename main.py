import os
import time
import random
import threading
from database import init_database
from video_downloader import get_download_link, download_video
from instagrapi import Client

def upload_video_to_account(username, password, video_path, caption):
    try:
        cl = Client()
        cl.login(username, password)
        cl.video_upload(video_path, caption)
        print(f"Uploaded: {video_path} to account: {username}")
    except Exception as e:
        print(f"Error uploading video for account {username}: {e}")

def process_account_videos(account, videos):
    username, password, purpose = account
    for index, video in enumerate(videos, start=1):
        video_purpose, link = video

        if video_purpose != purpose:
            continue

        download_url = get_download_link(link)
        if not download_url:
            print(f"Failed to get download URL for video: {link}")
            continue

        output_path = f"./videos/video_{index}.mp4"
        download_video(download_url, output_path)

        caption = f"Purpose: {purpose} #automatedupload"
        delay = random.randint(300, 1500)
        print(f"Waiting for {delay} seconds before uploading for account: {username}")
        time.sleep(delay)
        upload_video_to_account(username, password, output_path, caption)

def main():
    accounts, videos = init_database()

    threads = []
    for account in accounts:
        thread = threading.Thread(target=process_account_videos, args=(account, videos))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()