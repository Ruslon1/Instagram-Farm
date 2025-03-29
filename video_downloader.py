import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def get_download_link(tiktok_url):
    driver = setup_driver()
    driver.get("https://snaptik.app/en2")
    time.sleep(2)
    try:
        continue_button = driver.find_element(By.XPATH, '//button[contains(text(), "Continue")]')
        continue_button.click()
        input_field = driver.find_element(By.XPATH, '//input[@id="url"]')
        input_field.clear()
        input_field.send_keys(tiktok_url)
        download_button = driver.find_element(By.XPATH, '//button[contains(text(), "Download")]')
        download_button.click()
        time.sleep(5)
        download_link_element = driver.find_element(By.XPATH, '//a[contains(@class, "button download-file")]')
        download_url = download_link_element.get_attribute("href")
        return download_url
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
        print(f"Video downloaded to {output_path}")
    except Exception as e:
        print(f"Error downloading video: {e}")
