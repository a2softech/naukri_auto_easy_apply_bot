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


# **Function to get Firefox binary path automatically**
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


# **Auto-detect Firefox binary**
FIREFOX_BINARY_PATH = get_firefox_binary()
GECKODRIVER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "geckodriver.exe")

# **Logging setup**
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# **Firefox options configure karna**
options = Options()
options.binary_location = FIREFOX_BINARY_PATH
options.add_argument("--headless")  # Headless mode me run karna

# **WebDriver initialize karna**
service = Service(GECKODRIVER_PATH)
driver = webdriver.Firefox(service=service, options=options)
wait = WebDriverWait(driver, 10)

# **User se input lena URL ka**
url = input("Enter the job listing URL: ")
no_of_jobs_want_to_scrap = (int(input("Enter no of jobs you want to scrap: "))//20)
if not url:
    logging.error("No URL provided. Exiting...")
    driver.quit()
    exit()

# **URL open karna**
driver.get(url)

# **Folder setup**
folder_name = "Delete_me"
os.makedirs(folder_name, exist_ok=True)

# **CSV Filenames**
csv_filename = os.path.join(folder_name, "jobs.csv")
filter_csv_filename = os.path.join(folder_name, "jobs_filter.csv")

# === Files jaha se skip check karna hai ===
skip_files = {
    "already_applied.csv": "./Already_applied_folder/already_applied.csv",
    "skip_jobs.csv (4th col)": "./Already_applied_folder/skip_jobs.csv",
    "company_sites.csv": "./Already_applied_folder/company_sites.csv",
    "do_manually_apply.csv": "./Already_applied_folder/do_manually_apply.csv",
    "expired_jobs.csv": "./Already_applied_folder/expired_jobs.csv",
    "success_applied.csv": "./Already_applied_folder/success_applied.csv",
    "jobs.csv": csv_filename  # apna hi jobs.csv
}

# **Pehle se existing job links load karna**
existing_links = set()
skip_source_map = {}  # {link: "source"} to track reason

def load_links_from_file(file_path, source_name, column_index=0):
    """Generic function to load links from a csv file"""
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) > column_index:
                    link = row[column_index].strip()
                    if link:
                        existing_links.add(link)
                        skip_source_map[link] = source_name

# Load from all skip files
for source, path in skip_files.items():
    if "skip_jobs.csv" in source:  
        # 4th column wali file
        load_links_from_file(path, source, column_index=3)
    else:
        load_links_from_file(path, source, column_index=0)

# **Scraping configuration**
max_pages = ((no_of_jobs_want_to_scrap))
page_count = 0
data, filter_data = [], []
ScrapCounter = 0
TotalSkipped = 0

# Counters
skip_counts = {src: 0 for src in skip_files.keys()}


def safe_save():
    """Crash safety ke liye har step par data save"""
    if data:
        with open(csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerows(data)
        data.clear()

    if filter_data:
        file_exists = os.path.exists(filter_csv_filename)
        with open(filter_csv_filename, 'a', newline='', encoding='utf-8') as filterfile:
            csv_writer = csv.writer(filterfile)
            if not file_exists:
                csv_writer.writerow(["Company Name", "Experience Required", "Location", "Link"])
            csv_writer.writerows(filter_data)
        filter_data.clear()


try:
    while True:
        wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "srp-jobtuple-wrapper")))
        job_elements = driver.find_elements(By.CSS_SELECTOR, "div.srp-jobtuple-wrapper a.title")

        page_skip_count = 0

        for job_element in job_elements:
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

                # Skip condition with reason
                if job_link in existing_links:
                    reason = skip_source_map.get(job_link, "Unknown Source")
                    skip_counts[reason] = skip_counts.get(reason, 0) + 1
                    TotalSkipped += 1
                    page_skip_count += 1
                    logging.warning(f"⚠️ Skipped ({skip_counts[reason]} from {reason}): {job_link}")
                    continue

                # Add to set so duplicate na aaye
                existing_links.add(job_link)

                # Old jobs.csv ke liye
                data.append([job_link])

                # jobs_filter.csv ke liye
                filter_data.append([company, experience, location, job_link])

                ScrapCounter += 1
                logging.info(f"Extracted: {ScrapCounter} {job_title}")

                safe_save()

            except Exception as e:
                logging.error(f"Error extracting job data: {e}")

        if page_skip_count >= 20:
            max_pages += 1
            logging.info(f"🔄 Page {page_count+1}: {page_skip_count} skips found, increasing max_pages → {max_pages}")

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
    safe_save()

    # Final Summary
    logging.info("📊 Summary →")
    logging.info(f"Extracted: {ScrapCounter}")
    logging.info(f"Total Skipped: {TotalSkipped}")
    for source, count in skip_counts.items():
        logging.info(f"  {source}: {count}")
