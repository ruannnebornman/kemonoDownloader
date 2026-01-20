"""HTML parsing utilities for Kemono pages"""

import re
import logging
from typing import List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


class KemonoParser:
    """Parser for Kemono.cr HTML pages"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def parse_user_posts(self, html: str) -> List[str]:
        """
        Extract all post URLs from user page
        
        Args:
            html: HTML content of user page
            
        Returns:
            List of post URLs
        """
        soup = BeautifulSoup(html, 'lxml')
        post_urls = []
        
        # Posts are in <article> tags with links containing /post/
        articles = soup.find_all('article')
        
        for article in articles:
            link = article.find('a', href=re.compile(r'/post/\d+'))
            if link:
                href = link.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    if full_url not in post_urls:
                        post_urls.append(full_url)
        
        return post_urls
    
    def extract_post_id(self, url: str) -> Optional[str]:
        """
        Extract post ID from URL
        
        Args:
            url: Post URL
            
        Returns:
            Post ID or None
        """
        match = re.search(r'/post/(\d+)', url)
        return match.group(1) if match else None
    
    def parse_post_images(self, html: str) -> List[str]:
        """
        Extract all image URLs from post page
        
        Args:
            html: HTML content of post page
            
        Returns:
            List of image URLs
        """
        soup = BeautifulSoup(html, 'lxml')
        image_urls = []
        
        # Find all links that contain /data/ in href (full-resolution images)
        # These are the actual download links, not thumbnails
        data_links = soup.find_all('a', href=re.compile(r'/data/'))
        
        for link in data_links:
            href = link.get('href')
            if href and self._is_image_url(href):
                # URLs are already full URLs starting with https://n1.kemono.cr, etc.
                if href not in image_urls:
                    image_urls.append(href)
        
        return image_urls
    
    def _is_content_image(self, url: str) -> bool:
        """Check if URL is a content image (not icon/avatar/thumbnail)"""
        url_lower = url.lower()
        # Exclude common UI elements
        if any(x in url_lower for x in ['icon', 'avatar', 'logo', 'banner', 'static']):
            return False
        # Check if it's from data domain (actual content) - can be n1, n2, n3, n4, etc.
        if '/data/' in url_lower and 'kemono.cr' in url_lower:
            return True
        return self._is_image_url(url)
    
    def _is_image_url(self, url: str) -> bool:
        """Check if URL points to an image file"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']
        url_lower = url.lower()
        return any(ext in url_lower for ext in image_extensions)
    
    def has_next_page(self, html: str) -> Optional[str]:
        """
        Check if there's a next page of posts
        
        Args:
            html: HTML content of current page
            
        Returns:
            URL of next page or None
        """
        soup = BeautifulSoup(html, 'lxml')
        
        # Look for next button/link
        next_link = soup.find('a', string=re.compile(r'next', re.I))
        if next_link and next_link.get('href'):
            return urljoin(self.base_url, next_link['href'])
        
        # Look for pagination with rel="next"
        next_link = soup.find('a', rel='next')
        if next_link and next_link.get('href'):
            return urljoin(self.base_url, next_link['href'])
        
        return None
    
    def get_pagination_offset(self, html: str, current_offset: int = 0) -> Optional[int]:
        """
        Determine next pagination offset
        
        Args:
            html: HTML content
            current_offset: Current offset value
            
        Returns:
            Next offset or None if no more pages
        """
        soup = BeautifulSoup(html, 'lxml')
        
        # Look for the ">" (next) button which has the next offset
        next_button = soup.find('a', string='>')
        if next_button and next_button.get('href'):
            match = re.search(r'\?o=(\d+)', next_button['href'])
            if match:
                next_offset = int(match.group(1))
                # Only return if it's actually advancing
                if next_offset > current_offset:
                    return next_offset
        
        # Fallback: look for any pagination link with higher offset
        all_links = soup.find_all('a', href=re.compile(r'\?o=\d+'))
        max_offset = current_offset
        for link in all_links:
            match = re.search(r'\?o=(\d+)', link['href'])
            if match:
                offset = int(match.group(1))
                if offset > max_offset:
                    max_offset = offset
        
        if max_offset > current_offset:
            return current_offset + 50  # Kemono shows 50 posts per page
        
        return None

