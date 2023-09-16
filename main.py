import datetime
import os
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pyodbc

start_time = datetime.datetime.now()


class WebScraper:
    def __init__(self, website_url, num_pages, db_file):
        self.options = Options()
        self.options.add_argument("--headless")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("disable-infobars")
        self.options.add_argument("--remote-debugging-port=9222")
        self.driver = webdriver.Chrome(executable_path='/opt/google/chrome/google-chrome',service=Service(ChromeDriverManager().install()), options=self.options)
        self.website_url = website_url
        self.num_pages = num_pages
        self.db_file = db_file
        self.conn = self.create_database_connection()

    def create_database_connection(self):
        try:
            conn = pyodbc.connect(
                r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
                f'DBQ={self.db_file};'
            )
            return conn
        except pyodbc.Error as e:
            print(f"Database connection error: {e}")
            return None

    def save_to_database(self, row):
        if self.conn:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO ScrapedData2 (Name, ImageSrc, PromptOriginal, Model, Page)
                    VALUES (?, ?, ?, ?, ?)
                ''', row['Name'], row['Image Src'], row['Prompt - Original'], row['Model'], row['Page'])
                self.conn.commit()
                print("Data saved to the database successfully.")
            except pyodbc.Error as e:
                print(f"Error inserting data into the database: {e}")

    def extract_data(self):
        try:
            self.driver.get(self.website_url)
            window_width = self.driver.execute_script("return window.innerWidth;")
            window_height = self.driver.execute_script("return window.innerHeight;")

            center_x = window_width / 2
            center_y = window_height / 2

            actions = ActionChains(self.driver)
            actions.move_by_offset(center_x, center_y)
            actions.click().perform()
            self.website_url = self.driver.current_url

            image_locator = (By.CSS_SELECTOR, 'img[data-testid="image-post-image"]')
            model_locator = (By.CSS_SELECTOR, 'dl.text-gray-200 a')
            title_locator = (By.CSS_SELECTOR, 'h1.InputTitle_title__FTFOb')
            next_button_locator = (By.CSS_SELECTOR, 'button.circle-button.right-4')

            for page_number in range(self.num_pages):
                try:
                    print(f'Page {page_number + 1}')

                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'img[data-testid="image-post-image"]'))
                    )

                    image_element = self.driver.find_element(*image_locator)
                    image_src = image_element.get_attribute("src")
                    alt_text = image_element.get_attribute("alt").replace("Prompt: ", '')
                    model = self.driver.find_element(*model_locator).text
                    title = self.driver.find_element(*title_locator).text

                    new_row = {'Name': title, 'Image Src': image_src, 'Prompt - Original': alt_text, 'Model': model,
                               'Page': "Rising"}

                    # Insert the row into the database
                    self.save_to_database(new_row)

                    # Print elapsed time
                    noteTime(page_number)

                    # Click the next button to go to the next page
                    next_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(next_button_locator))
                    next_button.click()

                except Exception as e:
                    print()
                    print(f"Error on page {page_number + 1}: {e}")
                    print("Connection Issue: Moving to next")
                    print("Closing Connection and restarting ...")
                    self.driver.quit()

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            self.driver.quit()
            if self.conn:
                self.conn.close()


def noteTime(page_number):
    current_time = datetime.datetime.now()
    elapsed_time = current_time - start_time
    formatted_time = str(elapsed_time).split(".")[0]
    speed = "-"  # Calculate the speed (you can uncomment this line and calculate it if needed)
    print(f"Page {page_number + 1} - Time elapsed: {formatted_time} Speed - {speed} img/sec")


if __name__ == "__main__":
    driver_path = "./chromedriver.exe"
    website_url = 'https://playgroundai.com/feed'
    num_pages = 20000  # Number of pages to scrape
    db_file = r"db.accdb"  # Replace with your Access database file path

    scraper = WebScraper(website_url, num_pages, db_file)
    scraper.extract_data()
