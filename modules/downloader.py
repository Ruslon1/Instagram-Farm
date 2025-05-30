import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def get_download_link(tiktok_url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get("https://snaptik.app/en2")
        time.sleep(2)
        continue_button = driver.find_element(By.XPATH, '//button[contains(text(), "Continue")]')
        continue_button.click()
        input_field = driver.find_element(By.ID, "url")
        input_field.send_keys(tiktok_url)
        download_button = driver.find_element(By.XPATH, '//button[contains(text(), "Download")]')
        download_button.click()
        time.sleep(5)
        download_link = driver.find_element(By.XPATH, '//a[contains(@class, "button download-file")]').get_attribute("href")
        return download_link
    except Exception as e:
        print(f"Error retrieving download link: {e}")
        return None
    finally:
        driver.quit()

def download_video(download_url, output_path):
    try:
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Error downloading video: {e}")
        return False