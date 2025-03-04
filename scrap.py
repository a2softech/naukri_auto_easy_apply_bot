from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
import logging
import os


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Specify the path to GeckoDriver and Firefox binary
FIREFOX_BINARY_PATH = "C:\\Program Files\\Mozilla Firefox\\firefox.exe"  # Change if needed
GECKODRIVER_PATH = "./geckodriver.exe"  # Change if needed

# Configure Firefox options
options = Options()
options.binary_location = FIREFOX_BINARY_PATH
options.add_argument("--headless")  # Run in headless mode

# Initialize WebDriver
service = Service(GECKODRIVER_PATH)
driver = webdriver.Firefox(service=service, options=options)
wait = WebDriverWait(driver, 10)

# User input for target URL
url = input("Enter the job listing URL: ")
if not url:
    logging.error("No URL provided. Exiting...")
    driver.quit()
    exit()

# Open the URL
driver.get(url)

# Folder setup
folder_name = "Delete_me"
os.makedirs(folder_name, exist_ok=True)

# CSV Filenames
csv_filename = os.path.join(folder_name, "jobs.csv")
old_data_filename = "./Already_applied_folder/already_applied.csv"

# Load existing job links
existing_links = set()
if os.path.exists(old_data_filename):
    with open(old_data_filename, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        existing_links = {row[0] for row in reader}

# Set page limit
max_pages = 1
page_count = 0
data = []
ScrapCounter = 0

try:
    while True:
        wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "srp-jobtuple-wrapper")))
        job_elements = driver.find_elements(By.CSS_SELECTOR, "div.srp-jobtuple-wrapper a.title")

        for job_element in job_elements:
            try:
                job_link = job_element.get_attribute("href")
                job_title = job_element.text

                company = job_element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'srp-jobtuple-wrapper')]//a[contains(@class, 'comp-name')]").text or "Not Available"
                location = job_element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'srp-jobtuple-wrapper')]//span[contains(@class, 'locWdth')]").text or "Not Available"

                if job_link in existing_links:
                    continue

                data.append([job_link])
                ScrapCounter = ScrapCounter + 1
                logging.info(f"Extracted: {ScrapCounter} {job_title}")

            except Exception as e:
                logging.error(f"Error extracting job data: {e}")

        page_count += 1
        if page_count >= max_pages:
            logging.info("✅ Maximum page limit reached.")
            break

        try:
            next_button = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//a[contains(@class, 'styles_btn-secondary__2AsIP') and span[contains(text(), 'Next')]]")
            ))
            next_href = next_button.get_attribute("href")
            if next_href:
                driver.get(next_href)
                time.sleep(2)
            else:
                break
        except:
            break

finally:
    driver.quit()
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerows(data)
    logging.info(f"✅ CSV file '{csv_filename}' updated successfully!")
