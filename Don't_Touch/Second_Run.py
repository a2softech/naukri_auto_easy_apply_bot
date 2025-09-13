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
    profile_ini_path = os.path.expanduser("~/.mozilla/firefox/profiles.ini")
    if os.name == "nt":
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

FIREFOX_BINARY = get_firefox_binary()
PROFILE_PATH = get_firefox_profile()

current_time = datetime.now().strftime("%Y-%m-%d_%H")
already_applied_folder = "./Already_applied_folder"
os.makedirs(already_applied_folder, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

DRIVER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "geckodriver.exe")
CSV_FILE = "./Delete_me/jobs.csv"
COMPANY_SITES_CSV = os.path.join(already_applied_folder, "company_sites.csv")
FAILED_JOBS_CSV = os.path.join(already_applied_folder, "do_manually_apply.csv")
SUCCESS_APPLIED_CSV = os.path.join(already_applied_folder, "success_applied.csv")
ALREADY_APPLIED_CSV = os.path.join(already_applied_folder, "already_applied.csv")
EXPIRED_JOBS_CSV = os.path.join(already_applied_folder, "expired_jobs.csv")
# SKIP_JOBS_CSV removed ✅

success_apply = 0
error_apply = 0
already_applied = 0
company_sites_count = 0
expired_jobs_count = 0
# skip_job_custom removed ✅
line_no = 0

service = Service(DRIVER_PATH)
options = Options()
options.binary_location = FIREFOX_BINARY
options.add_argument("-profile")
options.add_argument(PROFILE_PATH)

driver = webdriver.Firefox(service=service, options=options)
wait = WebDriverWait(driver, 10)

company_sites_queue = queue.Queue()
failed_jobs_queue = queue.Queue()
success_applied_queue = queue.Queue()
already_applied_queue = queue.Queue()
expired_jobs_queue = queue.Queue()

company_sites_lock = threading.Lock()
failed_jobs_lock = threading.Lock()
success_applied_lock = threading.Lock()
already_applied_lock = threading.Lock()
expired_jobs_lock = threading.Lock()

def write_to_csv(file_path, queue, lock, headers):
    with lock:
        if not os.path.exists(file_path) or os.stat(file_path).st_size == 0:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)

    existing_data = set()
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader, None)
            for row in reader:
                if row:
                    existing_data.add(row[0])

    while True:
        data = queue.get()
        if data is None:
            break

        if data in existing_data:
            queue.task_done()
            continue

        with lock:
            with open(file_path, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([data])
            existing_data.add(data)

        queue.task_done()

company_thread = threading.Thread(target=write_to_csv, args=(COMPANY_SITES_CSV, company_sites_queue, company_sites_lock, ["URL"]))
failed_thread = threading.Thread(target=write_to_csv, args=(FAILED_JOBS_CSV, failed_jobs_queue, failed_jobs_lock, ["URL"]))
success_thread = threading.Thread(target=write_to_csv, args=(SUCCESS_APPLIED_CSV, success_applied_queue, success_applied_lock, ["URL"]))
already_applied_thread = threading.Thread(target=write_to_csv, args=(ALREADY_APPLIED_CSV, already_applied_queue, already_applied_lock, ["URL"]))
expired_jobs_thread = threading.Thread(target=write_to_csv, args=(EXPIRED_JOBS_CSV, expired_jobs_queue, expired_jobs_lock, ["URL"]))

company_thread.start()
failed_thread.start()
success_thread.start()
already_applied_thread.start()
expired_jobs_thread.start()

def load_urls_from_csv(file_path, column_index=0):
    if not os.path.exists(file_path):
        return set()
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader, None)
        urls = set()
        for row in reader:
            if len(row) > column_index:
                urls.add(row[column_index])
        return urls

already_applied_urls = load_urls_from_csv(ALREADY_APPLIED_CSV)
company_sites_urls = load_urls_from_csv(COMPANY_SITES_CSV)
expired_jobs_urls = load_urls_from_csv(EXPIRED_JOBS_CSV)
manual_jobs_urls = load_urls_from_csv(FAILED_JOBS_CSV)
# skip_jobs_urls removed ✅

with open(CSV_FILE, 'r', encoding='utf-8') as file:
    job_links = csv.reader(file)
    for job in job_links:
        job_url = job[0]

        if job_url in already_applied_urls:
            line_no += 1
            logging.info(f"{line_no} Skipping job (Already Applied)")
            continue
        if job_url in company_sites_urls:
            line_no += 1
            logging.info(f"{line_no} Skipping job (Company Site Exists)")
            continue
        if job_url in expired_jobs_urls:
            line_no += 1
            logging.info(f"{line_no} Skipping job (Expired Already)")
            continue
        if job_url in manual_jobs_urls:
            line_no += 1
            logging.info(f"{line_no} Skipping job (Manually Present)")
            continue
        # ✅ skip_jobs check removed

        driver.get(job_url)
        time.sleep(3)

        try:
            expired_element = driver.find_element(By.CLASS_NAME, "styles_alert-message-text__QwDRi")
            if expired_element and "expired" in expired_element.text.lower():
                expired_jobs_count += 1
                line_no += 1
                logging.info(f"{line_no} Job Expired (Skipping)")
                expired_jobs_queue.put(job_url)
                expired_jobs_urls.add(job_url)
                continue
        except NoSuchElementException:
            pass

        try:
            already_applied_element = driver.find_element(By.ID, "already-applied")
            if already_applied_element:
                line_no += 1
                already_applied += 1
                logging.info(f"{line_no} Already Applied Count: {already_applied}")
                already_applied_queue.put(job_url)
                already_applied_urls.add(job_url)
                continue
        except NoSuchElementException:
            pass

        company_site_buttons = driver.find_elements(By.ID, "company-site-button")
        if company_site_buttons:
            company_sites_count += 1
            line_no += 1
            logging.info(f"{line_no} Company Site Found (Skipping)")
            company_sites_queue.put(job_url)
            company_sites_urls.add(job_url)
            continue

        try:
            apply_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[text()='Apply']")))
            apply_button.click()

            wait.until(
                EC.any_of(
                    EC.presence_of_element_located((By.CLASS_NAME, "applied-job-content")),
                    EC.presence_of_element_located((By.CLASS_NAME, "apply-message"))
                )
            )
            success_apply += 1
            line_no += 1
            logging.info(f"{line_no} Successfully Applied")
            success_applied_queue.put(job_url)
        except TimeoutException:
            error_apply += 1
            line_no += 1
            logging.error(f"{line_no} Manually Apply Link")
            failed_jobs_queue.put(job_url)
            manual_jobs_urls.add(job_url)

company_sites_queue.put(None)
failed_jobs_queue.put(None)
success_applied_queue.put(None)
already_applied_queue.put(None)
expired_jobs_queue.put(None)

company_thread.join()
failed_thread.join()
success_thread.join()
already_applied_thread.join()
expired_jobs_thread.join()

driver.quit()
