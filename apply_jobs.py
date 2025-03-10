import json
import time
import csv
import logging
import os
import threading
import queue
import shutil
import configparser
from selenium.webdriver.firefox.service import Service
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime

# Function to get default Firefox profile
def get_firefox_profile():
    profile_ini_path = os.path.expanduser("~/.mozilla/firefox/profiles.ini")  # Linux/macOS
    if os.name == "nt":  # Windows
        profile_ini_path = os.path.join(os.getenv("APPDATA"), "Mozilla", "Firefox", "profiles.ini")

    config = configparser.ConfigParser()
    if os.path.exists(profile_ini_path):
        config.read(profile_ini_path)
        for section in config.sections():
            if config.has_option(section, "Default") and config.get(section, "Default") == "1":
                profile_path = config.get(section, "Path")
                return os.path.join(os.path.dirname(profile_ini_path), profile_path)

    raise Exception("No default Firefox profile found!")

# Function to get Firefox binary path
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

# Auto-detect Firefox binary and profile
FIREFOX_BINARY = get_firefox_binary()
PROFILE_PATH = get_firefox_profile()

# Create folders
current_time = datetime.now().strftime("%Y-%m-%d_%H")
already_applied_folder = "./Already_applied_folder"
os.makedirs(already_applied_folder, exist_ok=True)

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
DRIVER_PATH = "./geckodriver.exe"
CSV_FILE = "./Delete_me/jobs.csv"
COMPANY_SITES_CSV = os.path.join(already_applied_folder, "company_sites.csv")
FAILED_JOBS_CSV = os.path.join(already_applied_folder, "do_manually_apply.csv")  
SUCCESS_APPLIED_CSV = os.path.join(already_applied_folder, "success_applied.csv")  
ALREADY_APPLIED_CSV = os.path.join(already_applied_folder, "already_applied.csv")
MAX_APPLICATIONS = 500

# Initialize counters
success_apply = 0
error_apply = 0
already_applied = 0
company_sites_count = 0
skip_job_applied = 0

# Initialize WebDriver
service = Service(DRIVER_PATH)
options = Options()
options.binary_location = FIREFOX_BINARY
options.add_argument("-profile")
options.add_argument(PROFILE_PATH)

driver = webdriver.Firefox(service=service, options=options)
wait = WebDriverWait(driver, 10)

# Queues for async writing
company_sites_queue = queue.Queue()
failed_jobs_queue = queue.Queue()
success_applied_queue = queue.Queue()  
already_applied_queue = queue.Queue()

# Locks for thread safety
company_sites_lock = threading.Lock()
failed_jobs_lock = threading.Lock()
success_applied_lock = threading.Lock()  
already_applied_lock = threading.Lock()

# Function to write to CSV
def write_to_csv(file_path, queue, lock, headers):
    with lock:
        if not os.path.exists(file_path) or os.stat(file_path).st_size == 0:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)

    while True:
        data = queue.get()
        if data is None:
            break
        with lock:
            with open(file_path, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([data])
        queue.task_done()

# Start background threads
company_thread = threading.Thread(target=write_to_csv, args=(COMPANY_SITES_CSV, company_sites_queue, company_sites_lock, ["URL"]))
failed_thread = threading.Thread(target=write_to_csv, args=(FAILED_JOBS_CSV, failed_jobs_queue, failed_jobs_lock, ["URL"]))
success_thread = threading.Thread(target=write_to_csv, args=(SUCCESS_APPLIED_CSV, success_applied_queue, success_applied_lock, ["URL"]))  
already_applied_thread = threading.Thread(target=write_to_csv, args=(ALREADY_APPLIED_CSV, already_applied_queue, already_applied_lock, ["URL"]))

company_thread.start()
failed_thread.start()
success_thread.start()  
already_applied_thread.start()

# Load already applied URLs
def load_urls_from_csv(file_path):
    if not os.path.exists(file_path):
        return set()
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader, None)  # Skip header
        return {row[0] for row in reader}

already_applied_urls = load_urls_from_csv(ALREADY_APPLIED_CSV)
company_sites_urls = load_urls_from_csv(COMPANY_SITES_CSV)  # ✅ Load company sites

# Read CSV file
with open(CSV_FILE, 'r', encoding='utf-8') as file:
    job_links = csv.reader(file)
    for job in job_links:
        job_url = job[0]

        # ✅ Check if already applied or exists in company_sites.csv
        if job_url in already_applied_urls or job_url in company_sites_urls:
            skip_job_applied += 1
            logging.info(f"Skipping job (Already Applied/Company Site Exists): {skip_job_applied}")
            continue

        driver.get(job_url)
        time.sleep(3)

        # ✅ Check if already applied
        try:
            already_applied_element = driver.find_element(By.ID, "already-applied")
            if already_applied_element:
                already_applied += 1
                logging.info(f"Already Applied Count: {already_applied}")
                already_applied_queue.put(job_url)
                already_applied_urls.add(job_url)
                continue
        except NoSuchElementException:
            pass

        # ✅ Check if it is a company site
        company_site_buttons = driver.find_elements(By.ID, "company-site-button")
        if company_site_buttons:
            company_sites_count += 1
            logging.info(f"Company Site Found (Skipping): {company_sites_count}")
            company_sites_queue.put(job_url)
            company_sites_urls.add(job_url)  # ✅ Add to company_sites.csv
            continue

        # ✅ Try applying
        try:
            apply_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[text()='Apply']")))
            apply_button.click()

            success_message = wait.until(
                EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'successfully applied')]"))
            )
            success_apply += 1
            logging.info(f"Successfully Applied: {success_apply}")
            success_applied_queue.put(job_url)
        except TimeoutException:
            error_apply += 1
            logging.error(f"Manually Apply Link: {error_apply}")
            failed_jobs_queue.put(job_url)

# Stop threads
company_sites_queue.put(None)
failed_jobs_queue.put(None)
success_applied_queue.put(None)
already_applied_queue.put(None)

company_thread.join()
failed_thread.join()
success_thread.join()
already_applied_thread.join()

driver.quit()
