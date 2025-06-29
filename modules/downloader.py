import time
import requests
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from config.settings import settings


def get_download_link(tiktok_url):
    """Get download link for TikTok video using Selenium."""
    options = Options()

    # Add Chrome options from settings (исправляем использование)
    chrome_options_list = settings.get_chrome_options_list()
    for option in chrome_options_list:
        options.add_argument(option)

    # Additional Docker-specific options
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-features=TranslateUI")
    options.add_argument("--disable-ipc-flooding-protection")
    options.add_argument("--remote-debugging-port=9222")

    # Set Chrome binary location for Docker
    chrome_bin = os.environ.get('CHROME_BIN', '/usr/bin/chromium')
    if os.path.exists(chrome_bin):
        options.binary_location = chrome_bin

    # Set Chrome driver path
    chrome_driver = os.environ.get('CHROME_DRIVER', '/usr/bin/chromedriver')

    driver = None
    try:
        if os.path.exists(chrome_driver):
            # Use system Chrome driver (Docker)
            service = Service(chrome_driver)
        else:
            # Use WebDriver Manager (local development)
            service = Service(ChromeDriverManager().install())

        driver = webdriver.Chrome(service=service, options=options)

        # Set timeouts
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(10)

        print(f"🌐 Opening SnapTik for URL: {tiktok_url}")
        driver.get("https://snaptik.app/en2")

        # Wait for page load
        time.sleep(3)

        # Handle "Continue" button if present
        try:
            continue_button = driver.find_element(By.XPATH, '//button[contains(text(), "Continue")]')
            continue_button.click()
            time.sleep(2)
        except:
            print("ℹ️ No Continue button found, proceeding...")

        # Find and fill input field
        input_field = driver.find_element(By.ID, "url")
        input_field.clear()
        input_field.send_keys(tiktok_url)

        # Click download button
        download_button = driver.find_element(By.XPATH, '//button[contains(text(), "Download")]')
        download_button.click()

        # Wait for processing
        time.sleep(5)

        # Get download link
        download_link = driver.find_element(By.XPATH, '//a[contains(@class, "button download-file")]').get_attribute(
            "href")

        print(f"✅ Download link obtained: {download_link[:50]}...")
        return download_link

    except Exception as e:
        print(f"❌ Error retrieving download link: {e}")
        return None
    finally:
        if driver:
            driver.quit()


def download_video(download_url, output_path):
    """Download video from URL to local file."""
    try:
        print(f"📥 Downloading video to: {output_path}")

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Download with streaming
        response = requests.get(download_url, stream=True, timeout=60)
        response.raise_for_status()

        # Check content type
        content_type = response.headers.get('content-type', '')
        if 'video' not in content_type and 'octet-stream' not in content_type:
            print(f"⚠️ Unexpected content type: {content_type}")

        # Write file
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # Verify file was created and has content
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            file_size = os.path.getsize(output_path)
            print(f"✅ Video downloaded successfully: {file_size} bytes")
            return True
        else:
            print("❌ Downloaded file is empty or missing")
            return False

    except requests.exceptions.Timeout:
        print("❌ Download timeout")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Download error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error downloading video: {e}")
        return False