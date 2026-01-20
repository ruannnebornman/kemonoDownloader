#!/usr/bin/env python3
"""
Kemono Downloader - Download all images from Kemono.cr user posts

Usage:
    python main.py --user-id 167293545
    python main.py --user-id 167293545 --output ./my_downloads
"""

import argparse
import sys
import asyncio
import logging
from typing import List, Dict

from config import DOWNLOAD_DIR, LOG_FILE, LOG_LEVEL
from scraper_selenium import KemonoSeleniumScraper
from downloader_async import AsyncImageDownloader
from utils import setup_logging, create_directory

logger = logging.getLogger(__name__)


async def async_main(args):
    """Async main function"""
    
    logger.info("="*60)
    logger.info("Kemono Downloader Starting")
    logger.info("="*60)
    logger.info(f"User ID: {args.user_id}")
    logger.info(f"Output directory: {args.output}")
    
    # Update config if needed
    if args.no_skip_existing:
        import config
        config.SKIP_EXISTING = False
    
    # Create output directory
    if not create_directory(args.output):
        logger.error(f"Failed to create output directory: {args.output}")
        sys.exit(1)
    
    try:
        # Initialize scraper and downloader
        scraper = KemonoSeleniumScraper(headless=True)
        downloader = AsyncImageDownloader(args.output)
        
        # Phase 1: Get all post URLs
        logger.info("\n" + "="*60)
        logger.info("PHASE 1: Fetching post URLs")
        logger.info("="*60)
        post_urls = scraper.get_user_posts(args.user_id)
        
        if not post_urls:
            logger.error("No posts found for this user")
            sys.exit(1)
        
        logger.info(f"Found {len(post_urls)} posts")
        
        # Apply max-posts limit if specified
        if args.max_posts and len(post_urls) > args.max_posts:
            logger.info(f"Limiting to first {args.max_posts} posts")
            post_urls = post_urls[:args.max_posts]
        
        # Phase 2: Extract images from all posts concurrently (in batches)
        logger.info("\n" + "="*60)
        logger.info("PHASE 2: Extracting images from posts (parallel batches)")
        logger.info("="*60)
        
        from concurrent.futures import ThreadPoolExecutor
        import concurrent.futures
        import threading
        
        # Thread-local storage for selenium drivers
        thread_local = threading.local()
        
        def get_thread_scraper():
            """Get or create a scraper for this thread"""
            if not hasattr(thread_local, "scraper"):
                thread_local.scraper = KemonoSeleniumScraper(headless=True)
            return thread_local.scraper
        
        def process_post_sync(idx, post_url):
            """Process a single post to extract images (runs in thread)"""
            try:
                thread_scraper = get_thread_scraper()
                post_info = thread_scraper.get_post_info(post_url)
                images = thread_scraper.get_post_images(post_url)
                
                if images:
                    return {
                        'post_id': post_info['id'],
                        'images': images
                    }
            except Exception as e:
                logger.error(f"Error processing post {idx}: {e}")
            return None
        
        def cleanup_thread_scraper():
            """Cleanup scraper for this thread"""
            if hasattr(thread_local, "scraper"):
                try:
                    thread_local.scraper.close()
                except:
                    pass
        
        # Process posts in parallel using thread pool (5 threads for stability)
        print(f"\nExtracting images from {len(post_urls)} posts (5 threads)...")
        posts_data = []
        
        with ThreadPoolExecutor(max_workers=5, initializer=lambda: None) as executor:
            # Submit all tasks
            future_to_post = {
                executor.submit(process_post_sync, idx, url): (idx, url) 
                for idx, url in enumerate(post_urls, 1)
            }
            
            # Process as they complete
            completed = 0
            for future in concurrent.futures.as_completed(future_to_post):
                completed += 1
                idx, url = future_to_post[future]
                print(f"\rProcessed {completed}/{len(post_urls)} posts...", end='', flush=True)
                
                try:
                    result = future.result()
                    if result:
                        posts_data.append(result)
                except Exception as e:
                    logger.error(f"Error getting result for post {idx}: {e}")
        
        print()  # New line after progress
        print()  # New line after progress
        
        total_images = sum(len(p['images']) for p in posts_data)
        
        logger.info(f"Found {total_images} images across {len(posts_data)} posts")
        print(f"Found {total_images} images across {len(posts_data)} posts")
        
        if total_images == 0:
            logger.warning("No images found to download")
            return
        
        # Phase 3: Download all images
        logger.info("\n" + "="*60)
        logger.info("PHASE 3: Downloading images (async with rate limiting)")
        logger.info("="*60)
        
        total_downloaded = await downloader.download_user_images(args.user_id, posts_data)
        logger.info(f"\nTotal images downloaded: {total_downloaded}")
        
        # Print summary
        downloader.print_summary()
        
        logger.info("\n" + "="*60)
        logger.info("Download Complete!")
        logger.info("="*60)
        
        # Cleanup
        scraper.close()
        
    except KeyboardInterrupt:
        logger.info("\nDownload interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


def main():
    """Entry point that runs async main"""
    parser = argparse.ArgumentParser(
        description='Download all images from Kemono.cr user posts'
    )
    parser.add_argument(
        '--user-id',
        required=True,
        help='User ID from Kemono.cr (e.g., 167293545)'
    )
    parser.add_argument(
        '--output',
        default=DOWNLOAD_DIR,
        help=f'Output directory (default: {DOWNLOAD_DIR})'
    )
    parser.add_argument(
        '--log-file',
        default=LOG_FILE,
        help='Log file path'
    )
    parser.add_argument(
        '--log-level',
        default=LOG_LEVEL,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )
    parser.add_argument(
        '--no-skip-existing',
        action='store_true',
        help='Re-download existing files'
    )
    parser.add_argument(
        '--max-posts',
        type=int,
        default=None,
        help='Maximum number of posts to process (useful for testing, default: all)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_file, args.log_level)
    
    # Run async main
    asyncio.run(async_main(args))


if __name__ == '__main__':
    main()
