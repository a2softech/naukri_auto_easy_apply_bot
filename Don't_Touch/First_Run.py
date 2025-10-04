import os
import csv
import time
import shutil
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ================================
# 🔹 Function to get Firefox binary
# ================================
def get_firefox_binary():
    firefox_path = shutil.which("firefox")
    if firefox_path:
        return firefox_path
    else:
        possible_paths = [
            "C:\\Program Files\\Mozilla Firefox\\firefox.exe",
            "C:\\Program Files (x86)\\Mozilla Firefox\\firefox.exe"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        raise Exception("Firefox binary not found! Please check your installation.")

# ================================
# 🔹 Auto detect paths
# ================================
FIREFOX_BINARY_PATH = get_firefox_binary()
GECKODRIVER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "geckodriver.exe")

# ================================
# 🔹 Logging setup
# ================================
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ================================
# 🔹 Firefox options
# ================================
options = Options()
options.binary_location = FIREFOX_BINARY_PATH
options.add_argument("--headless")

service = Service(GECKODRIVER_PATH)
driver = webdriver.Firefox(service=service, options=options)
wait = WebDriverWait(driver, 10)

# ================================
# 🔹 User Input
# ================================
url = input("Enter the job listing URL: ").strip()
target_jobs = int(input("Enter number of jobs you want to scrape: "))

if not url:
    logging.error("No URL provided. Exiting...")
    driver.quit()
    exit()

driver.get(url)

# ================================
# 🔹 Folder Setup
# ================================
folder_name = "Delete_me"
os.makedirs(folder_name, exist_ok=True)

csv_filename = os.path.join(folder_name, "jobs.csv")
filter_csv_filename = os.path.join(folder_name, "jobs_filter.csv")

# ================================
# 🔹 Skip Files Configuration
# ================================
skip_files = {
    "already_applied.csv": "./Already_applied_folder/already_applied.csv",
    "skip_jobs.csv (4th col)": "./Already_applied_folder/skip_jobs.csv",
    "company_sites.csv": "./Already_applied_folder/company_sites.csv",
    "do_manually_apply.csv": "./Already_applied_folder/do_manually_apply.csv",
    "expired_jobs.csv": "./Already_applied_folder/expired_jobs.csv",
    "success_applied.csv": "./Already_applied_folder/success_applied.csv",
    "jobs.csv": csv_filename
}

existing_links = set()
skip_source_map = {}

# ================================
# 🔹 Function to load skip links
# ================================
def load_links_from_file(file_path, source_name, column_index=0):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) > column_index:
                    link = row[column_index].strip()
                    if link:
                        existing_links.add(link)
                        skip_source_map[link] = source_name

for source, path in skip_files.items():
    if "skip_jobs.csv" in source:
        load_links_from_file(path, source, column_index=3)
    else:
        load_links_from_file(path, source, column_index=0)

# ================================
# 🔹 Counters and Data Holders
# ================================
filter_data = []
ScrapCounter = 0
TotalSkipped = 0
skip_counts = {src: 0 for src in skip_files.keys()}

# ================================
# 🔹 Safe Save Function
# ================================
def safe_save():
    if filter_data:
        headers = ["Company Name", "Experience Required", "Location", "Link"]

        for file_path in [csv_filename, filter_csv_filename]:
            file_exists = os.path.exists(file_path)
            with open(file_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(headers)
                writer.writerows(filter_data)

        filter_data.clear()

# ================================
# 🔹 Scraping Loop (Count-Based)
# ================================
try:
    while ScrapCounter < target_jobs:
        wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "srp-jobtuple-wrapper")))
        job_elements = driver.find_elements(By.CSS_SELECTOR, "div.srp-jobtuple-wrapper a.title")

        for job_element in job_elements:
            if ScrapCounter >= target_jobs:
                break  # stop once target reached

            try:
                job_link = job_element.get_attribute("href")
                job_title = job_element.text

                wrapper = job_element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'srp-jobtuple-wrapper')]")
                company = wrapper.find_element(By.XPATH, ".//a[contains(@class, 'comp-name')]").text or "Not Available"
                location = wrapper.find_element(By.XPATH, ".//span[contains(@class, 'locWdth')]").text or "Not Available"

                try:
                    experience = wrapper.find_element(By.XPATH, ".//span[contains(@class, 'expwdth')]").text
                except:
                    experience = "Not Available"

                # Skip duplicate links
                if job_link in existing_links:
                    reason = skip_source_map.get(job_link, "Unknown Source")
                    skip_counts[reason] = skip_counts.get(reason, 0) + 1
                    TotalSkipped += 1
                    logging.warning(f"⚠️ Skipped ({skip_counts[reason]} from {reason}): {job_link}")
                    continue

                existing_links.add(job_link)

                filter_data.append([company, experience, location, job_link])
                ScrapCounter += 1
                logging.info(f"✅ Extracted {ScrapCounter}: {job_title}")

                safe_save()

            except Exception as e:
                logging.error(f"Error extracting job data: {e}")

        # Stop if enough jobs found
        if ScrapCounter >= target_jobs:
            break

        # Try next page
        try:
            next_button = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//a[contains(@class, 'styles_btn-secondary__2AsIP') and span[contains(text(), 'Next')]]")
            ))
            next_href = next_button.get_attribute("href")
            if next_href:
                driver.get(next_href)
                time.sleep(2)
            else:
                logging.info("🚫 No next page available.")
                break
        except:
            logging.info("🚫 Next button not found. Exiting pagination.")
            break

finally:
    driver.quit()
    safe_save()

    logging.info("📊 Final Summary →")
    logging.info(f"Extracted Jobs: {ScrapCounter}")
    logging.info(f"Skipped Jobs: {TotalSkipped}")
    for source, count in skip_counts.items():
        logging.info(f"  {source}: {count}")
    logging.info("✅ Completed Successfully.")
