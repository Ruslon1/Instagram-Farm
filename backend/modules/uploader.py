from pathlib import Path
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired, PleaseWaitFewMinutes, RecaptchaChallengeForm
from modules.logger import telegram_notify
from modules.proxy_utils import get_account_proxy_config, get_instagrapi_proxy_settings
import time
import random
import requests
import os

SESSION_DIR = Path("./sessions")
SESSION_DIR.mkdir(exist_ok=True)


def get_session_path(username: str) -> Path:
    """Get session file path for username."""
    return SESSION_DIR / f"{username}.session"


def upload_video_to_instagram(username: str, password: str, video_path: str, caption: str,
                              token: str, chat_id: str, two_fa_key: str = None) -> bool:
    """Upload video to Instagram with proxy support."""
    try:
        print(f"🔄 Starting upload for @{username}")

        # Initialize Instagram client
        cl = Client()
        cl.delay_range = [1, 3]
        cl.request_timeout = 30

        # Configure proxy if available
        proxy_config = get_account_proxy_config(username)
        if proxy_config and proxy_config.get('active'):
            try:
                proxy_settings = get_instagrapi_proxy_settings(proxy_config)
                cl.set_proxy(proxy_settings['proxy'])
                if 'proxy_port' in proxy_settings:
                    cl.proxy_port = proxy_settings['proxy_port']
                if 'proxy_username' in proxy_settings:
                    cl.proxy_username = proxy_settings['proxy_username']
                if 'proxy_password' in proxy_settings:
                    cl.proxy_password = proxy_settings['proxy_password']

                print(f"🌐 Using proxy: {proxy_config['host']}:{proxy_config['port']}")
            except Exception as e:
                print(f"⚠️ Failed to set proxy for @{username}: {e}")
                # Continue without proxy

        session_path = get_session_path(username)

        # Try to use existing session
        if session_path.exists():
            try:
                print(f"🔑 Loading existing session for @{username}")
                cl.load_settings(session_path)

                # Test session validity
                cl.get_timeline_feed()
                print(f"✅ Session valid for @{username}")

            except (LoginRequired, Exception) as e:
                print(f"⚠️ Session expired for @{username}, logging in...")
                session_path.unlink(missing_ok=True)  # Remove invalid session

                # Perform fresh login
                if not perform_login(cl, username, password, two_fa_key, session_path):
                    return False
        else:
            # No session exists, perform fresh login
            print(f"🔑 No session found for @{username}, logging in...")
            if not perform_login(cl, username, password, two_fa_key, session_path):
                return False

        # Verify video file exists
        if not os.path.exists(video_path):
            print(f"❌ Video file not found: {video_path}")
            return False

        file_size = os.path.getsize(video_path)
        if file_size == 0:
            print(f"❌ Video file is empty: {video_path}")
            return False

        print(f"📱 Uploading video ({file_size} bytes) to @{username}")

        # Add random delay before upload
        delay = random.uniform(5, 15)
        print(f"⏳ Waiting {delay:.1f} seconds before upload...")
        time.sleep(delay)

        # Upload video
        media = cl.video_upload(video_path, caption)

        if media:
            print(f"✅ Video uploaded successfully to @{username}")
            print(f"📸 Media ID: {media.pk}")
            return True
        else:
            print(f"❌ Upload failed for @{username} - no media returned")
            return False

    except Exception as e:
        error_msg = str(e).lower()
        print(f"❌ Error uploading video for @{username}: {e}")

        # Send error notification
        telegram_notify(token, chat_id, f"❌ Upload error for @{username}: {e}")

        # Handle login-related errors
        if any(keyword in error_msg for keyword in ['login', 'challenge', 'checkpoint', 'session']):
            try:
                print(f"🧹 Removing session file for @{username}")
                session_path = get_session_path(username)
                session_path.unlink(missing_ok=True)
            except Exception as cleanup_error:
                print(f"⚠️ Error removing session file: {cleanup_error}")

        return False


def perform_login(cl: Client, username: str, password: str, two_fa_key: str = None,
                  session_path: Path = None) -> bool:
    """Perform Instagram login with 2FA support."""
    try:
        # Add random delay
        delay = random.uniform(2, 5)
        print(f"⏳ Waiting {delay:.1f} seconds before login...")
        time.sleep(delay)

        if two_fa_key:
            print(f"🔐 Getting 2FA code for @{username}")

            # Get 2FA code from service
            response = requests.get(f"https://2fa.fb.rip/api/otp/{two_fa_key}", timeout=10)
            response.raise_for_status()

            fa_data = response.json()
            if fa_data.get("ok"):
                fa_code = fa_data["data"]["otp"]
                print(f"🔑 2FA code obtained: {fa_code}")

                # Login with 2FA
                cl.login(username, password, verification_code=fa_code)
            else:
                raise Exception(f"Failed to get 2FA code: {fa_data}")
        else:
            # Regular login
            print(f"🔑 Logging in @{username} without 2FA")
            cl.login(username, password)

        # Save session if login successful
        if session_path:
            cl.dump_settings(session_path)
            print(f"💾 Session saved for @{username}")

        print(f"✅ Login successful for @{username}")
        return True

    except requests.RequestException as e:
        print(f"❌ 2FA service error for @{username}: {e}")
        return False
    except Exception as e:
        print(f"❌ Login failed for @{username}: {e}")
        return False


def test_instagram_connection(username: str, password: str, two_fa_key: str = None) -> bool:
    """Test Instagram connection and create session without uploading."""
    try:
        print(f"🧪 Testing Instagram connection for @{username}")

        cl = Client()
        cl.delay_range = [1, 3]
        cl.request_timeout = 30

        # Configure proxy if available
        proxy_config = get_account_proxy_config(username)
        if proxy_config and proxy_config.get('active'):
            try:
                proxy_settings = get_instagrapi_proxy_settings(proxy_config)
                cl.set_proxy(proxy_settings['proxy'])
                if 'proxy_port' in proxy_settings:
                    cl.proxy_port = proxy_settings['proxy_port']
                if 'proxy_username' in proxy_settings:
                    cl.proxy_username = proxy_settings['proxy_username']
                if 'proxy_password' in proxy_settings:
                    cl.proxy_password = proxy_settings['proxy_password']
                print(f"🌐 Testing with proxy: {proxy_config['host']}:{proxy_config['port']}")
            except Exception as e:
                print(f"⚠️ Proxy setup failed, testing without proxy: {e}")

        session_path = get_session_path(username)

        # Try login and create session
        if perform_login(cl, username, password, two_fa_key, session_path):
            # Test basic API calls to verify everything works
            try:
                # Get user info
                user_info = cl.user_info_by_username(username)
                print(f"✅ Connection test successful for @{username}")
                print(f"📊 Account info: {user_info.follower_count} followers")

                # Test timeline feed
                timeline = cl.get_timeline_feed()
                print(f"📱 Timeline feed accessible: {len(timeline)} items")

                return True
            except Exception as api_error:
                print(f"❌ API test failed for @{username}: {api_error}")
                # Clean up session if API tests fail
                try:
                    session_path.unlink(missing_ok=True)
                except:
                    pass
                return False
        else:
            return False

    except ChallengeRequired as e:
        print(f"❌ Challenge required for @{username}: {e}")
        print("📋 Account may need to complete security challenge manually")
        return False
    except PleaseWaitFewMinutes as e:
        print(f"⏰ Rate limit for @{username}: {e}")
        print("📋 Instagram is asking to wait - try again later")
        return False
    except RecaptchaChallengeForm as e:
        print(f"🤖 reCAPTCHA challenge for @{username}: {e}")
        print("📋 Account may need manual verification")
        return False
    except Exception as e:
        print(f"❌ Connection test failed for @{username}: {e}")

        # Clean up any created session files on error
        try:
            session_path = get_session_path(username)
            session_path.unlink(missing_ok=True)
        except:
            pass

        return False


def cleanup_session(username: str):
    """Remove session file for username."""
    try:
        session_path = get_session_path(username)
        if session_path.exists():
            session_path.unlink()
            print(f"🧹 Session cleaned up for @{username}")
    except Exception as e:
        print(f"⚠️ Error cleaning up session for @{username}: {e}")


def verify_session_exists(username: str) -> bool:
    """Check if session file exists for username."""
    session_path = get_session_path(username)
    return session_path.exists()


def get_session_info(username: str) -> dict:
    """Get information about existing session."""
    session_path = get_session_path(username)

    if not session_path.exists():
        return {
            "exists": False,
            "path": str(session_path),
            "size": 0,
            "created": None
        }

    try:
        stat = session_path.stat()
        return {
            "exists": True,
            "path": str(session_path),
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime
        }
    except Exception as e:
        return {
            "exists": True,
            "path": str(session_path),
            "error": str(e)
        }


def validate_session(username: str) -> bool:
    """Validate existing session by testing it."""
    session_path = get_session_path(username)

    if not session_path.exists():
        print(f"❌ No session file for @{username}")
        return False

    try:
        cl = Client()
        cl.load_settings(session_path)

        # Test session validity
        cl.get_timeline_feed()
        print(f"✅ Session valid for @{username}")
        return True

    except Exception as e:
        print(f"❌ Session invalid for @{username}: {e}")
        return False