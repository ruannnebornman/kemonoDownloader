"""Image download functionality"""

import os
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional
import requests
from tqdm import tqdm

from config import (
    DOWNLOAD_DIR, MAX_RETRIES, RETRY_DELAY, TIMEOUT,
    USER_AGENT, SKIP_EXISTING, VERIFY_SSL
)
from utils import (
    sanitize_filename, create_directory,
    get_file_extension, format_bytes
)

logger = logging.getLogger(__name__)


class ImageDownloader:
    """Download and save images from URLs"""
    
    def __init__(self, output_dir: str = DOWNLOAD_DIR):
        self.output_dir = output_dir
        self.stats = {
            'total': 0,
            'downloaded': 0,
            'skipped': 0,
            'failed': 0,
            'bytes': 0
        }
    
    def download_user_images(self, user_id: str, posts_data: List[Dict]) -> Dict:
        """
        Download all images for a user's posts
        
        Args:
            user_id: User ID
            posts_data: List of dicts with 'post_id' and 'images' keys
            
        Returns:
            Statistics dictionary
        """
        user_dir = os.path.join(self.output_dir, f"user_{user_id}")
        create_directory(user_dir)
        
        logger.info(f"Starting download for user {user_id}")
        logger.info(f"Total posts: {len(posts_data)}")
        
        # Count total images
        total_images = sum(len(post['images']) for post in posts_data)
        self.stats['total'] = total_images
        
        logger.info(f"Total images to download: {total_images}")
        
        # Progress bar for overall progress
        with tqdm(total=total_images, desc="Downloading images", unit="img") as pbar:
            for post_data in posts_data:
                post_id = post_data['post_id']
                images = post_data['images']
                
                if not images:
                    continue
                
                # Create post directory
                post_dir = os.path.join(user_dir, f"post_{post_id}")
                create_directory(post_dir)
                
                # Download images for this post
                for idx, image_url in enumerate(images, 1):
                    success = self.download_image(
                        image_url,
                        post_dir,
                        idx
                    )
                    
                    if success:
                        self.stats['downloaded'] += 1
                    
                    pbar.update(1)
                    time.sleep(0.1)  # Small delay between downloads
        
        return self.get_stats()
    
    def download_image(self, url: str, save_dir: str, index: int) -> bool:
        """
        Download a single image
        
        Args:
            url: Image URL
            save_dir: Directory to save the image
            index: Image index for naming
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate filename
            filename = self._generate_filename(url, index)
            filepath = os.path.join(save_dir, filename)
            
            # Skip if file exists
            if SKIP_EXISTING and os.path.exists(filepath):
                logger.debug(f"Skipping existing file: {filename}")
                self.stats['skipped'] += 1
                return True
            
            # Download with retries
            for attempt in range(MAX_RETRIES):
                try:
                    response = requests.get(
                        url,
                        timeout=TIMEOUT,
                        verify=VERIFY_SSL,
                        headers={'User-Agent': USER_AGENT},
                        stream=True
                    )
                    response.raise_for_status()
                    
                    # Save image
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    file_size = os.path.getsize(filepath)
                    self.stats['bytes'] += file_size
                    
                    logger.debug(f"Downloaded: {filename} ({format_bytes(file_size)})")
                    return True
                    
                except requests.exceptions.RequestException as e:
                    if attempt < MAX_RETRIES - 1:
                        logger.warning(f"Retry {attempt + 1}/{MAX_RETRIES} for {url}: {e}")
                        time.sleep(RETRY_DELAY)
                    else:
                        raise
            
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            self.stats['failed'] += 1
            return False
    
    def _generate_filename(self, url: str, index: int) -> str:
        """
        Generate filename for image
        
        Args:
            url: Image URL
            index: Image index
            
        Returns:
            Sanitized filename
        """
        # Try to get original filename from URL
        original_name = url.split('/')[-1].split('?')[0]
        
        # Get extension
        ext = get_file_extension(url)
        
        # If we have a good original name, use it
        if original_name and len(original_name) > 5:
            filename = sanitize_filename(original_name)
        else:
            # Use index-based naming
            filename = f"image_{index:03d}{ext}"
        
        return filename
    
    def get_stats(self) -> Dict:
        """Get download statistics"""
        return {
            **self.stats,
            'success_rate': (self.stats['downloaded'] / self.stats['total'] * 100) 
                           if self.stats['total'] > 0 else 0,
            'total_size': format_bytes(self.stats['bytes'])
        }
    
    def print_summary(self):
        """Print download summary"""
        stats = self.get_stats()
        print("\n" + "="*50)
        print("DOWNLOAD SUMMARY")
        print("="*50)
        print(f"Total images:     {stats['total']}")
        print(f"Downloaded:       {stats['downloaded']}")
        print(f"Skipped:          {stats['skipped']}")
        print(f"Failed:           {stats['failed']}")
        print(f"Success rate:     {stats['success_rate']:.1f}%")
        print(f"Total size:       {stats['total_size']}")
        print("="*50)
