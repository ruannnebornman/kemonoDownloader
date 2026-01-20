"""Selenium-based scraper for Kemono (handles JavaScript rendering)"""

import time
import logging
from typing import List, Optional, Dict
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from config import BASE_URL, REQUEST_DELAY, TIMEOUT
from parser import KemonoParser

logger = logging.getLogger(__name__)


class KemonoSeleniumScraper:
    """Scraper for Kemono.cr website using Selenium"""
    
    def __init__(self, headless: bool = True):
        self.base_url = BASE_URL
        self.parser = KemonoParser(BASE_URL)
        self.driver = self._create_driver(headless)
    
    def _create_driver(self, headless: bool) -> webdriver.Chrome:
        """Create and configure Chrome WebDriver"""
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument('--headless=new')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Suppress logging
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(TIMEOUT)
            return driver
        except WebDriverException as e:
            logger.error(f"Failed to create Chrome driver: {e}")
            logger.info("Make sure Chrome/Chromium and chromedriver are installed")
            raise
    
    def get_user_posts(self, user_id: str) -> List[str]:
        """
        Get all post URLs for a user
        
        Args:
            user_id: User ID from Kemono
            
        Returns:
            List of post URLs
        """
        all_posts = []
        offset = 0
        page = 1
        
        logger.info(f"Fetching posts for user {user_id}")
        
        while True:
            url = f"{self.base_url}/patreon/user/{user_id}"
            if offset > 0:
                url += f"?o={offset}"
            
            logger.info(f"Fetching page {page} (offset: {offset})")
            
            try:
                html = self._fetch_page(url)
                if not html:
                    break
                
                # Parse posts from current page
                posts = self.parser.parse_user_posts(html)
                
                if not posts:
                    logger.info("No more posts found")
                    break
                
                # Add new posts (avoid duplicates)
                new_posts = [p for p in posts if p not in all_posts]
                all_posts.extend(new_posts)
                
                logger.info(f"Found {len(new_posts)} new posts (total: {len(all_posts)})")
                
                # Check for next page
                next_offset = self.parser.get_pagination_offset(html, offset)
                if next_offset is None or next_offset == offset:
                    break
                
                offset = next_offset
                page += 1
                time.sleep(REQUEST_DELAY)
                
            except Exception as e:
                logger.error(f"Error fetching posts page {page}: {e}")
                break
        
        logger.info(f"Total posts found: {len(all_posts)}")
        return all_posts
    
    def get_post_images(self, post_url: str) -> List[str]:
        """
        Get all image URLs from a post
        
        Args:
            post_url: URL of the post
            
        Returns:
            List of image URLs
        """
        logger.info(f"Fetching images from post: {post_url}")
        
        try:
            html = self._fetch_page(post_url)
            if not html:
                return []
            
            images = self.parser.parse_post_images(html)
            logger.info(f"Found {len(images)} images in post")
            return images
            
        except Exception as e:
            logger.error(f"Error fetching post images: {e}")
            return []
    
    def get_post_info(self, post_url: str) -> Dict[str, str]:
        """
        Get basic info about a post
        
        Args:
            post_url: URL of the post
            
        Returns:
            Dictionary with post info (id, url)
        """
        post_id = self.parser.extract_post_id(post_url)
        return {
            'id': post_id or 'unknown',
            'url': post_url
        }
    
    def _fetch_page(self, url: str, wait_for_selector: str = 'article') -> Optional[str]:
        """
        Fetch HTML content from URL using Selenium
        
        Args:
            url: URL to fetch
            wait_for_selector: CSS selector to wait for before getting HTML
            
        Returns:
            HTML content or None if failed
        """
        try:
            self.driver.get(url)
            
            # Wait for content to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_selector))
                )
            except TimeoutException:
                logger.warning(f"Timeout waiting for {wait_for_selector} on {url}")
                # Continue anyway, might still have content
            
            # Small delay to ensure everything is loaded
            time.sleep(1)
            
            # Get the page source
            html = self.driver.page_source
            return html
            
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
