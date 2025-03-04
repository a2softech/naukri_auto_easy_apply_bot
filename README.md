# Automated Job Application Bot

## Overview
This script automates the process of applying to job listings using **Selenium** and **threading**. It navigates through job listings, checks for already applied jobs, applies to new ones, and categorizes job URLs accordingly. The script uses **Firefox WebDriver** and requires a **Firefox profile** for seamless browsing.

## Features
✅ Automatically applies to jobs from a CSV file.  
✅ Skips jobs that are already applied.  
✅ Detects job postings that redirect to company websites.  
✅ Logs application status and saves categorized job links.  
✅ Uses multi-threading for efficient CSV writing.  
✅ Saves application history to avoid duplicate applications.  

## Installation
### 1. Clone the Repository
```sh
git clone https://github.com/your-username/job-auto-apply.git
cd job-auto-apply
```

### 2. Install Dependencies
Make sure you have Python installed. Then, install required libraries:
```sh
pip install selenium
```

### 3. Download & Setup GeckoDriver
- Download **GeckoDriver** from [Mozilla](https://github.com/mozilla/geckodriver/releases).
- Extract it and place it in the project directory.

### 4. Configure Firefox Profile
The script automatically detects your default **Firefox profile**. If needed, manually set your profile path in the script.

## Usage
1. Prepare a **jobs.csv** file inside the `Delete_me` folder with job listing URLs. Example:
```
https://jobportal.com/job1
https://jobportal.com/job2
```
2. Run the script:
```sh
python main.py
```
3. The script will:
   - Open each job link in **Firefox**.
   - Check if already applied.
   - Try to apply if possible.
   - Log successful, failed, and skipped applications.

## Output Files
- `company_sites.csv` - Jobs that redirect to company websites.
- `failed_jobs.csv` - Jobs where application failed.
- `already_applied.csv` - Jobs already applied.
- Logs are displayed in the terminal for progress tracking.

## Contributing
Pull requests are welcome! If you find issues, feel free to report them.

## License
This project is licensed under the **MIT License**.

---
🚀 Happy job hunting automation! 🎯

