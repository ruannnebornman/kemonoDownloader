"""Configuration settings for Kemono Downloader"""

# Base settings
BASE_URL = "https://kemono.cr"
DOWNLOAD_DIR = "./downloads"

# Request settings
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
REQUEST_DELAY = 1  # seconds between requests
TIMEOUT = 30  # seconds
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Download settings
MAX_CONCURRENT_DOWNLOADS = 5
SKIP_EXISTING = True  # Skip already downloaded files
VERIFY_SSL = True

# Logging
LOG_FILE = "kemono_downloader.log"
LOG_LEVEL = "INFO"
