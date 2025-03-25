import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def setup_driver():
    # Configure Selenium to use headless Chrome
    chrome_options = Options()
    # Uncomment for headless mode
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--enable-unsafe-swiftshader")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def download_video_file(download_url, output_path):
    try:
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Video downloaded and saved to {output_path}")
    except Exception as e:
        print(f"Error downloading video: {e}")

def get_download_link(tiktok_url):
    driver = setup_driver()  # Create a new browser session
    driver.get("https://snaptik.app/en2")
    time.sleep(2)  # Wait for the page to load

    try:
        continue_button = driver.find_element(By.XPATH, '//button[contains(text(), "Continue")]')
        continue_button.click()
        # Locate the input field and enter the TikTok URL
        input_field = driver.find_element(By.XPATH, '//input[@id="url"]')
        input_field.clear()
        input_field.send_keys(tiktok_url)
        
        # Locate and click the download button
        download_button = driver.find_element(By.XPATH, '//button[contains(text(), "Download")]')
        download_button.click()
        
        # Wait for the processing to complete and the download link to appear
        time.sleep(5)
        
        # Extract the download link
        download_link_element = driver.find_element(By.XPATH, '//a[contains(@class, "button download-file")]')
        download_url = download_link_element.get_attribute("href")
        return download_url
    except Exception as e:
        print(f"Error retrieving download link for {tiktok_url}: {e}")
        return None
    finally:
        driver.quit()  # Close the browser session

def main():
    input_file = "links.txt"  # File containing TikTok video URLs
    output_dir = "./video"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    if not os.path.exists(input_file):
        print(f"File {input_file} not found.")
        return
    
    with open(input_file, "r") as file:
        links = [line.strip() for line in file if line.strip()]
    
    for index, tiktok_url in enumerate(links, start=1):
        print(f"Processing ({index}/{len(links)}): {tiktok_url}")
        download_url = get_download_link(tiktok_url)  # New browser session per link
        if download_url:
            output_path = os.path.join(output_dir, f"video_{index}_no_watermark.mp4")
            download_video_file(download_url, output_path)
        else:
            print(f"Failed to retrieve the download URL for {tiktok_url}")
    
    print("All videos processed.")

if __name__ == "__main__":
    main()
