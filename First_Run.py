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
import shutil


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
GECKODRIVER_PATH = "./geckodriver.exe"  # GeckoDriver ka path

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
old_data_filename = "./Already_applied_folder/already_applied.csv"

# **Pehle se existing job links load karna**
existing_links = set()

# already_applied.csv load
if os.path.exists(old_data_filename):
    with open(old_data_filename, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                existing_links.add(row[0])

# jobs.csv load
if os.path.exists(csv_filename):
    with open(csv_filename, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                existing_links.add(row[0])

# **Scraping configuration**
max_pages = 50
page_count = 0
data = []
filter_data = []
ScrapCounter = 0
TotalSkipped = 0

try:
    while True:
        wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "srp-jobtuple-wrapper")))
        job_elements = driver.find_elements(By.CSS_SELECTOR, "div.srp-jobtuple-wrapper a.title")

        page_skip_count = 0  # NEW: per-page skip counter

        for job_element in job_elements:
            try:
                job_link = job_element.get_attribute("href")
                job_title = job_element.text

                wrapper = job_element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'srp-jobtuple-wrapper')]")
                company = wrapper.find_element(By.XPATH, ".//a[contains(@class, 'comp-name')]").text or "Not Available"
                location = wrapper.find_element(By.XPATH, ".//span[contains(@class, 'locWdth')]").text or "Not Available"
                
                # NEW: Experience Required extract karna
                try:
                    experience = wrapper.find_element(By.XPATH, ".//span[contains(@class, 'expwdth')]").text
                except:
                    experience = "Not Available"

                if job_link in existing_links:
                    logging.warning(f"⚠️ Skipped (already exists): {job_link}")
                    page_skip_count += 1
                    TotalSkipped += 1
                    continue

                # Old jobs.csv ke liye
                data.append([job_link])

                # jobs_filter.csv ke liye
                filter_data.append([company, experience, location, job_link])

                ScrapCounter += 1
                logging.info(f"Extracted: {ScrapCounter} {job_title}")

            except Exception as e:
                logging.error(f"Error extracting job data: {e}")

        # ✅ Agar ek page me 20 ya usse zyada skip hue to max_pages +1
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

    # === jobs.csv append mode ===
    if data:
        with open(csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerows(data)
        logging.info(f"✅ {len(data)} new records added in jobs.csv")
    else:
        logging.info("ℹ️ No new records for jobs.csv")

    # === jobs_filter.csv append mode ===
    if filter_data:
        file_exists = os.path.exists(filter_csv_filename)
        with open(filter_csv_filename, 'a', newline='', encoding='utf-8') as filterfile:
            csv_writer = csv.writer(filterfile)
            # Agar file pehle nahi hai tabhi header likhe
            if not file_exists:
                csv_writer.writerow(["Company Name", "Experience Required", "Location", "Link"])
            csv_writer.writerows(filter_data)
        logging.info(f"✅ {len(filter_data)} new records added in jobs_filter.csv")
    else:
        logging.info("ℹ️ No new records for jobs_filter.csv")

    # === Final Summary ===
    logging.info(f"📊 Summary → Extracted: {ScrapCounter}, Skipped: {TotalSkipped}, Added: {len(data)}")
