"""Async image download functionality with proper rate limiting"""

import os
import asyncio
import time
import logging
from pathlib import Path
from typing import List, Dict
import aiohttp
import aiofiles
from tqdm.asyncio import tqdm

from config import (
    DOWNLOAD_DIR, MAX_CONCURRENT_DOWNLOADS, TIMEOUT,
    USER_AGENT, SKIP_EXISTING, VERIFY_SSL,
    RATE_LIMIT_DELAY, BATCH_SIZE, BATCH_PAUSE
)
from utils import (
    sanitize_filename, create_directory,
    get_file_extension, format_bytes
)

logger = logging.getLogger(__name__)


class AsyncImageDownloader:
    """Async download and save images from URLs with rate limiting"""
    
    def __init__(self, output_dir: str = DOWNLOAD_DIR):
        self.output_dir = output_dir
        self.stats = {
            'total': 0,
            'downloaded': 0,
            'skipped': 0,
            'failed': 0,
            'bytes': 0
        }
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)
        self.last_download_time = 0
    
    async def download_user_images(self, user_id: str, posts_data: List[Dict]) -> Dict:
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
        
        logger.info(f"Starting async download for user {user_id}")
        logger.info(f"Total posts: {len(posts_data)}")
        
        # Count total images
        total_images = sum(len(post['images']) for post in posts_data)
        self.stats['total'] = total_images
        
        logger.info(f"Total images to download: {total_images}")
        logger.info(f"Max concurrent downloads: {MAX_CONCURRENT_DOWNLOADS}")
        logger.info(f"Rate limit: {RATE_LIMIT_DELAY}s between requests")
        
        # Create async session
        connector = aiohttp.TCPConnector(limit=MAX_CONCURRENT_DOWNLOADS)
        timeout = aiohttp.ClientTimeout(total=TIMEOUT)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': USER_AGENT}
        ) as session:
            # Create all download tasks
            tasks = []
            for post_data in posts_data:
                post_id = post_data['post_id']
                images = post_data['images']
                
                if not images:
                    continue
                
                # Create post directory
                post_dir = os.path.join(user_dir, f"post_{post_id}")
                create_directory(post_dir)
                
                # Create tasks for this post's images
                for idx, image_url in enumerate(images, 1):
                    task = self.download_image(session, image_url, post_dir, idx)
                    tasks.append(task)
            
            # Download with progress bar and batching
            await self._download_with_batches(tasks)
        
        return self.stats['downloaded']
    
    async def _download_with_batches(self, tasks: List):
        """
        Download tasks in batches with pauses to avoid overwhelming server
        
        Args:
            tasks: List of download tasks
        """
        total = len(tasks)
        
        with tqdm(total=total, desc="Downloading images", unit="img") as pbar:
            for i in range(0, total, BATCH_SIZE):
                batch = tasks[i:i + BATCH_SIZE]
                
                # Run batch concurrently
                results = await asyncio.gather(*batch, return_exceptions=True)
                
                # Update progress bar
                pbar.update(len(batch))
                
                # Pause between batches (except for the last batch)
                if i + BATCH_SIZE < total:
                    logger.debug(f"Batch complete. Pausing for {BATCH_PAUSE}s...")
                    await asyncio.sleep(BATCH_PAUSE)
    
    async def download_image(self, session: aiohttp.ClientSession, url: str, 
                            save_dir: str, index: int) -> bool:
        """
        Download a single image
        
        Args:
            session: aiohttp session
            url: Image URL
            save_dir: Directory to save the image
            index: Image index for naming
            
        Returns:
            True if successful, False otherwise
        """
        # Generate filename
        filename = self._generate_filename(url, index)
        filepath = os.path.join(save_dir, filename)
        
        # Skip if file exists
        if SKIP_EXISTING and os.path.exists(filepath):
            logger.debug(f"Skipping existing file: {filename}")
            self.stats['skipped'] += 1
            return True
        
        # Rate limiting - ensure minimum delay between downloads
        async with self.semaphore:
            # Wait for rate limit
            current_time = time.time()
            time_since_last = current_time - self.last_download_time
            if time_since_last < RATE_LIMIT_DELAY:
                await asyncio.sleep(RATE_LIMIT_DELAY - time_since_last)
            
            self.last_download_time = time.time()
            
            try:
                # Download image
                async with session.get(url, ssl=VERIFY_SSL) as response:
                    response.raise_for_status()
                    
                    # Write to file
                    async with aiofiles.open(filepath, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                
                file_size = os.path.getsize(filepath)
                self.stats['bytes'] += file_size
                self.stats['downloaded'] += 1
                
                logger.debug(f"Downloaded: {filename} ({format_bytes(file_size)})")
                return True
                
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
