import os
import shutil
import configparser
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

# Constants
DRIVER_PATH = "./geckodriver.exe"
NAUKRI_URL = "https://www.naukri.com/mnjuser/homepage"

# Initialize WebDriver
service = Service(DRIVER_PATH)
options = Options()
options.binary_location = FIREFOX_BINARY
options.add_argument("-profile")
options.add_argument(PROFILE_PATH)

driver = webdriver.Firefox(service=service, options=options)
wait = WebDriverWait(driver, 10)

try:
    # Open Naukri homepage
    driver.get(NAUKRI_URL)
    
    # Click on Profile Dropdown
    profile_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.nI-gNb-drawer__icon")))
    profile_button.click()

    # Click Logout Button
    logout_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Logout')]")))
    logout_button.click()

    print("Successfully logged out from Naukri.com")

except Exception as e:
    print(f"Error: {e}")

finally:
    driver.quit()
