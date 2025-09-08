import os
import shutil
import configparser
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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

# ✅ geckodriver.exe Don't_Touch के अंदर है
DRIVER_PATH = os.path.join(BASE_DIR, "geckodriver.exe")
NAUKRI_URL = "https://www.naukri.com/mnjuser/homepage"

service = Service(DRIVER_PATH)
options = Options()
options.binary_location = FIREFOX_BINARY
options.add_argument("-profile")
options.add_argument(PROFILE_PATH)

driver = webdriver.Firefox(service=service, options=options)
wait = WebDriverWait(driver, 10)

try:
    driver.get(NAUKRI_URL)

    profile_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.nI-gNb-drawer__icon")))
    profile_button.click()

    logout_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Logout')]")))
    logout_button.click()

    print("✅ Successfully logged out from Naukri.com")

except Exception as e:
    print(f"(Probably already logged out) Info: {e}")

finally:
    driver.quit()
