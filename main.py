#!/usr/bin/env python3
"""
Kemono Downloader - Download all images from Kemono.cr user posts

Usage:
    python main.py --user-id 167293545
    python main.py --user-id 167293545 --output ./my_downloads
"""

import argparse
import sys
import logging
from typing import List, Dict

from config import DOWNLOAD_DIR, LOG_FILE, LOG_LEVEL
from scraper_selenium import KemonoSeleniumScraper
from downloader import ImageDownloader
from utils import setup_logging, create_directory

logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
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
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_file, args.log_level)
    
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
        downloader = ImageDownloader(args.output)
        
        # Phase 1: Get all post URLs
        logger.info("\n" + "="*60)
        logger.info("PHASE 1: Fetching post URLs")
        logger.info("="*60)
        post_urls = scraper.get_user_posts(args.user_id)
        
        if not post_urls:
            logger.error("No posts found for this user")
            sys.exit(1)
        
        logger.info(f"Found {len(post_urls)} posts")
        
        # Phase 2: Get images from each post
        logger.info("\n" + "="*60)
        logger.info("PHASE 2: Extracting image URLs from posts")
        logger.info("="*60)
        
        posts_data = []
        for idx, post_url in enumerate(post_urls, 1):
            logger.info(f"Processing post {idx}/{len(post_urls)}")
            
            post_info = scraper.get_post_info(post_url)
            images = scraper.get_post_images(post_url)
            
            if images:
                posts_data.append({
                    'post_id': post_info['id'],
                    'images': images
                })
        
        total_images = sum(len(p['images']) for p in posts_data)
        logger.info(f"Found {total_images} images across {len(posts_data)} posts")
        
        if total_images == 0:
            logger.warning("No images found to download")
            sys.exit(0)
        
        # Phase 3: Download all images
        logger.info("\n" + "="*60)
        logger.info("PHASE 3: Downloading images")
        logger.info("="*60)
        
        downloader.download_user_images(args.user_id, posts_data)
        
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


if __name__ == '__main__':
    main()
