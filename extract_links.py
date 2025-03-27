import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time

def get_tiktok_links(username, video_count=20):
    options = Options()
    #options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    
    service = Service("./chromedriver-win64/chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options)

    tiktok_url = f"https://www.tiktok.com/@{username}"

    try:
        driver.get(tiktok_url)
        time.sleep(5)

        for _ in range(5):
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
            time.sleep(2)

        video_elements = driver.find_elements(By.XPATH, "//a[contains(@href, '/video/')]")
        video_links = [video.get_attribute('href') for video in video_elements]

        return video_links[:video_count]

    finally:
        driver.quit()


def insert_links_to_db(db_name, table_name, purpose, links):
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()

    values = [(purpose, link) for link in links]

    try:
        cursor.executemany(f"INSERT INTO {table_name} (Purpose, Link) VALUES (?, ?)", values)
        connection.commit()
        print("Ссылки успешно добавлены в базу данных!")
    except sqlite3.Error as error:
        print("Ошибка при работе с SQLite:", error)
    finally:
        connection.close()


if __name__ == "__main__":
    username = "theclipstudiox"
    db_name = "database.sqlite"
    table_name = "Videos"
    purpose = "Speed"

    links = get_tiktok_links(username)

    if links:
        insert_links_to_db(db_name, table_name, purpose, links)
    else:
        print("Не удалось найти ссылки на видео.")