"""Core scraping functionality for Kemono"""

import time
import logging
from typing import List, Optional, Dict
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import (
    BASE_URL, MAX_RETRIES, RETRY_DELAY, REQUEST_DELAY,
    TIMEOUT, USER_AGENT, VERIFY_SSL
)
from parser import KemonoParser

logger = logging.getLogger(__name__)


class KemonoScraper:
    """Scraper for Kemono.cr website"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.parser = KemonoParser(BASE_URL)
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic"""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=RETRY_DELAY,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set headers
        session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        return session
    
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
    
    def _fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch HTML content from URL
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or None if failed
        """
        try:
            response = self.session.get(
                url,
                timeout=TIMEOUT,
                verify=VERIFY_SSL
            )
            response.raise_for_status()
            return response.text
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def close(self):
        """Close the session"""
        self.session.close()
