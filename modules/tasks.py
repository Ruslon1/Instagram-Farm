from celery import Task
from celery_app import app
from modules.downloader import get_download_link, download_video
from modules.uploader import upload_video_to_instagram
from modules.logger import telegram_notify
from modules.database import record_publication, is_video_published
from services.task_service import TaskService
import os
import random
import time
import hashlib
import json
import asyncio
from datetime import datetime
from celery.exceptions import Ignore


class ProgressTask(Task):
    """Custom Celery task with progress tracking and cancellation support"""

    def __init__(self):
        self.should_stop = False

    def update_progress(self, current: int, total: int, current_item: str, cooldown: int = None):
        """Update task progress with detailed info"""
        progress_percent = int((current / total) * 100) if total > 0 else 0

        message = f"Processing {current}/{total}: {current_item}"
        if cooldown:
            message += f" (Next in {cooldown}s)"

        # Update database with progress info using Celery task ID
        asyncio.run(TaskService.update_task_progress(
            task_id=self.request.id,  # Use Celery task ID
            progress=progress_percent,
            current_item=current_item,
            message=message,
            cooldown_seconds=cooldown
        ))

    def check_if_cancelled(self):
        """Check if task should be cancelled"""
        task_info = asyncio.run(TaskService.get_task_progress(self.request.id))
        if task_info and task_info.status == "cancelled":
            self.should_stop = True
            return True
        return False

    def cancel_task(self):
        """Cancel the current task"""
        self.should_stop = True
        asyncio.run(TaskService.update_task_status(
            task_id=self.request.id,
            status="cancelled",
            message="Task cancelled by user"
        ))


# Keep original function for backward compatibility
@app.task(bind=True, max_retries=3)
def process_video(self, account, videos, telegram_token, chat_id):
    """Original video processing function (kept for compatibility)"""
    username, password, theme, two_fa_key = account
    captions = []
    with open("captions.json", "r") as outfile:
        captions = json.load(outfile)

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

        caption = random.choice(
            captions) + "\n#vlogging#beach#layingdown#whereatcomefrom#green#sand#red#ishowspeed#red#sunny#gettingtothebag#55154#subscribers#daily#wegotthis#sofunny"
        upload_result = upload_video_to_instagram(username, password, output_path, caption, telegram_token, chat_id,
                                                  two_fa_key)
        cooldown = random.randint(300, 1500)
        if upload_result:
            telegram_notify(telegram_token, chat_id,
                            f"Successfully uploaded video from: {video} to account: {username}. Cooldown = {cooldown} s")
            record_publication(username, video)
            os.remove(output_path)
        else:
            telegram_notify(telegram_token, chat_id, f"Failed to upload video from: {video} to account: {username}")

        time.sleep(cooldown)


# Enhanced function with detailed progress tracking and cancellation
@app.task(bind=True, base=ProgressTask, max_retries=3)
def process_video_with_progress(self, account, videos, telegram_token, chat_id):
    """Enhanced video processing with detailed progress tracking and cancellation support"""
    username, password, theme, two_fa_key = account
    total_videos = len(videos)

    # Initialize task logging with Celery task ID
    asyncio.run(TaskService.log_task(
        task_id=self.request.id,  # Use Celery task ID directly
        task_type="upload",
        status="running",
        account_username=username,
        message=f"Starting upload of {total_videos} videos to @{username}",
        total_items=total_videos,
        progress=0
    ))

    # Load captions
    captions = []
    try:
        with open("captions.json", "r") as outfile:
            captions = json.load(outfile)
    except Exception as e:
        captions = ["Default caption #video #content"]
        print(f"Could not load captions: {e}")

    success_count = 0
    failed_count = 0

    for i, video in enumerate(videos, 1):
        # Check for cancellation at the start of each video
        if self.check_if_cancelled():
            telegram_notify(telegram_token, chat_id,
                            f"🛑 Upload task cancelled for @{username} after {i - 1}/{total_videos} videos")
            raise Ignore()

        current_video_name = f"Video {i}"

        try:
            # Update progress - starting this video
            self.update_progress(i, total_videos, f"Checking if {current_video_name} was already posted")

            # Check if already published
            if is_video_published(username, video):
                asyncio.run(TaskService.update_task_progress(
                    task_id=self.request.id,
                    progress=int((i / total_videos) * 100),
                    current_item=f"{current_video_name} - Already posted, skipping",
                    message=f"Skipped {current_video_name} (already posted)"
                ))
                continue

            # Check for cancellation before download
            if self.check_if_cancelled():
                telegram_notify(telegram_token, chat_id,
                                f"🛑 Upload task cancelled for @{username} during {current_video_name}")
                raise Ignore()

            # Update progress - getting download link
            self.update_progress(i, total_videos, f"Getting download link for {current_video_name}")

            download_url = get_download_link(video)
            if not download_url:
                failed_count += 1
                asyncio.run(TaskService.update_task_progress(
                    task_id=self.request.id,
                    progress=int((i / total_videos) * 100),
                    current_item=f"{current_video_name} - Failed to get download link",
                    message=f"Failed to get download link for {current_video_name}"
                ))
                telegram_notify(telegram_token, chat_id, f"❌ Failed to get download link: {video}")
                continue

            # Update progress - downloading video
            self.update_progress(i, total_videos, f"Downloading {current_video_name}")

            unique_hash = hashlib.md5(f"{username}_{video}".encode()).hexdigest()
            output_path = f"./videos/{unique_hash}.mp4"
            success = download_video(download_url, output_path)

            if not success:
                failed_count += 1
                asyncio.run(TaskService.update_task_progress(
                    task_id=self.request.id,
                    progress=int((i / total_videos) * 100),
                    current_item=f"{current_video_name} - Download failed",
                    message=f"Failed to download {current_video_name}"
                ))
                telegram_notify(telegram_token, chat_id, f"❌ Failed to download: {video}")
                continue

            # Check for cancellation before upload
            if self.check_if_cancelled():
                # Clean up downloaded file
                try:
                    os.remove(output_path)
                except:
                    pass
                telegram_notify(telegram_token, chat_id,
                                f"🛑 Upload task cancelled for @{username} before uploading {current_video_name}")
                raise Ignore()

            # Update progress - uploading to Instagram
            self.update_progress(i, total_videos, f"Uploading {current_video_name} to Instagram")

            caption = random.choice(
                captions) + "\n#vlogging#beach#layingdown#whereatcomefrom#green#sand#red#ishowspeed#red#sunny#gettingtothebag#55154#subscribers#daily#wegotthis#sofunny"

            upload_result = upload_video_to_instagram(username, password, output_path, caption, telegram_token, chat_id,
                                                      two_fa_key)

            if upload_result:
                success_count += 1

                # Calculate cooldown for next video
                cooldown = random.randint(300, 1500) if i < total_videos else 0

                # Update progress - upload successful, waiting cooldown
                if cooldown > 0:
                    self.update_progress(
                        i, total_videos,
                        f"{current_video_name} uploaded successfully - Waiting {cooldown}s cooldown",
                        cooldown
                    )
                else:
                    self.update_progress(
                        i, total_videos,
                        f"{current_video_name} uploaded successfully - All done!",
                        0
                    )

                # Record publication
                record_publication(username, video)

                # Clean up video file
                try:
                    os.remove(output_path)
                except:
                    pass

                # Send success notification
                telegram_notify(
                    telegram_token, chat_id,
                    f"✅ Successfully uploaded {current_video_name} to @{username}\n"
                    f"📊 Progress: {i}/{total_videos}\n"
                    f"⏱️ Cooldown: {cooldown}s"
                )

                # Wait cooldown period with live updates and cancellation checks
                if cooldown > 0:
                    remaining = cooldown
                    while remaining > 0:
                        # Check for cancellation during cooldown
                        if self.check_if_cancelled():
                            telegram_notify(telegram_token, chat_id,
                                            f"🛑 Upload task cancelled for @{username} during cooldown")
                            raise Ignore()

                        wait_time = min(10, remaining)
                        time.sleep(wait_time)
                        remaining -= wait_time

                        if remaining > 0:
                            self.update_progress(
                                i, total_videos,
                                f"{current_video_name} uploaded - Cooldown remaining: {remaining}s",
                                remaining
                            )

            else:
                failed_count += 1
                asyncio.run(TaskService.update_task_progress(
                    task_id=self.request.id,
                    progress=int((i / total_videos) * 100),
                    current_item=f"{current_video_name} - Upload failed",
                    message=f"Failed to upload {current_video_name}"
                ))
                telegram_notify(telegram_token, chat_id, f"❌ Failed to upload {current_video_name} to @{username}")

                # Clean up failed video file
                try:
                    os.remove(output_path)
                except:
                    pass

        except Ignore:
            # Task was cancelled, re-raise to stop execution
            raise
        except Exception as e:
            failed_count += 1
            error_msg = f"Error processing {current_video_name}: {str(e)}"

            asyncio.run(TaskService.update_task_progress(
                task_id=self.request.id,
                progress=int((i / total_videos) * 100),
                current_item=f"{current_video_name} - Error occurred",
                message=error_msg
            ))

            telegram_notify(telegram_token, chat_id, f"❌ {error_msg}")
            continue

    # Task completion
    final_message = f"✅ Upload task completed for @{username}\n📊 Results: {success_count} successful, {failed_count} failed out of {total_videos} total"

    asyncio.run(TaskService.update_task_status(
        task_id=self.request.id,
        status="success" if success_count > 0 else "failed",
        message=final_message
    ))

    telegram_notify(telegram_token, chat_id, final_message)

    return {
        "success_count": success_count,
        "failed_count": failed_count,
        "total_videos": total_videos,
        "account": username
    }