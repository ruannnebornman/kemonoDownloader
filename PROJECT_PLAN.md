# Kemono Downloader - Project Plan

## Overview
A Python-based web scraper to download all images from kemono.cr for a given user, organizing them into structured folders.

## Requirements
- Input: User ID (e.g., 167293545)
- Output: Organized folder structure with all images
- Target: https://kemono.cr/patreon/user/{user_id}

## Folder Structure
```
downloads/
├── user_{user_id}/
│   ├── post_{post_id_1}/
│   │   ├── image_001.png
│   │   ├── image_002.jpg
│   │   └── ...
│   ├── post_{post_id_2}/
│   │   └── ...
│   └── ...
```

## Technology Stack

### Primary Options
1. **Python + Requests + BeautifulSoup4** (Recommended for static content)
   - Pros: Fast, lightweight, easy to use
   - Cons: May not work if site uses heavy JavaScript

2. **Python + Selenium/Playwright** (If dynamic content)
   - Pros: Handles JavaScript rendering
   - Cons: Slower, more resource-intensive

### Additional Libraries
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `lxml` - Fast HTML/XML parser
- `pathlib` - File path handling
- `tqdm` - Progress bars
- `urllib.parse` - URL handling

## Application Architecture

### Module Structure
```
kemono_downloader/
├── main.py                  # Entry point
├── scraper.py              # Core scraping logic
├── downloader.py           # Image download handling
├── parser.py               # HTML parsing utilities
├── config.py               # Configuration settings
├── utils.py                # Helper functions
└── requirements.txt        # Dependencies
```

### Core Classes

#### 1. KemonoScraper
```python
class KemonoScraper:
    - get_user_posts(user_id) -> List[post_urls]
    - get_post_images(post_url) -> List[image_urls]
    - handle_pagination() -> Iterator
```

#### 2. ImageDownloader
```python
class ImageDownloader:
    - download_image(url, save_path) -> bool
    - batch_download(image_urls, folder_path)
    - resume_download() # Handle interrupted downloads
```

#### 3. FileManager
```python
class FileManager:
    - create_directory_structure(user_id, post_id)
    - check_existing_files() # Skip already downloaded
    - sanitize_filename(filename)
```

## Detailed Workflow

### Phase 1: Fetch User Posts
1. Navigate to user page: `https://kemono.cr/patreon/user/{user_id}`
2. Parse HTML to find all post links
3. Handle pagination (if exists):
   - Look for "Next" button or page numbers
   - Query parameter like `?o=25` for offset
4. Extract all post IDs and URLs
5. Store in list/queue for processing

### Phase 2: Process Each Post
For each post URL:
1. Navigate to post page: `https://kemono.cr/patreon/user/{user_id}/post/{post_id}`
2. Parse HTML to find all image elements
3. Extract image URLs (could be in `<img>` tags, links, or embedded)
4. Handle different image URL formats:
   - Direct URLs: `https://n1.kemono.cr/data/...`
   - Thumbnails vs full resolution
5. Filter out non-image URLs

### Phase 3: Download Images
For each image:
1. Create folder structure: `downloads/user_{user_id}/post_{post_id}/`
2. Check if image already exists (skip if yes)
3. Download image with proper naming
4. Verify download integrity (check file size, try to open)
5. Handle download failures with retry logic

### Phase 4: Error Recovery
- Log all operations
- Save progress state
- Resume from last successful download

## Key Implementation Details

### 1. User Posts Extraction
```python
# Strategy:
- Look for <a> tags with href containing "/post/"
- Pattern: /patreon/user/{user_id}/post/{post_id}
- May need to handle lazy loading/infinite scroll
```

### 2. Image URL Extraction
```python
# Possible locations:
- <img src="..."> tags
- <a href="..."> download links
- Background images in CSS
- JSON data in <script> tags
```

### 3. Pagination Handling
```python
# Check for:
- Query parameters: ?o=0, ?o=25, ?o=50 (offset)
- "Load more" button with AJAX calls
- Infinite scroll requiring scrolling simulation
```

### 4. Rate Limiting
```python
# Be respectful to server:
- Add delays between requests (0.5-2 seconds)
- Use exponential backoff on errors
- Implement max concurrent downloads
```

### 5. File Naming Convention
```python
# Options:
- Keep original filename from URL
- Sequential naming: image_001.png, image_002.jpg
- Hash-based: {hash}.{extension}
- Include metadata: {post_id}_{index}_{original_name}
```

## Error Handling & Edge Cases

### Network Issues
- Connection timeouts
- 404 errors (deleted posts/images)
- 429 rate limiting
- Server errors (500, 502, 503)
- SSL/TLS errors

### Content Issues
- Empty posts (no images)
- Private/restricted content
- Paywalled content
- Video files (decide: skip or download?)
- Embedded content from external sites

### File System Issues
- Disk space full
- Permission errors
- Invalid characters in filenames
- Path length limits (Windows)

## Configuration Options

### config.py
```python
BASE_URL = "https://kemono.cr"
DOWNLOAD_DIR = "./downloads"
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
REQUEST_DELAY = 1  # seconds between requests
TIMEOUT = 30  # seconds
USER_AGENT = "Mozilla/5.0 ..."
MAX_CONCURRENT_DOWNLOADS = 5
SKIP_EXISTING = True  # Skip already downloaded files
VERIFY_SSL = True
```

## Usage Example

### Command Line Interface
```bash
# Download all posts for a user
python main.py --user-id 167293545

# With options
python main.py --user-id 167293545 --output ./my_downloads --delay 2

# Resume interrupted download
python main.py --user-id 167293545 --resume

# Specific posts only
python main.py --user-id 167293545 --posts 148605353,148605354
```

### Programmatic Usage
```python
from kemono_downloader import KemonoDownloader

downloader = KemonoDownloader()
downloader.download_user(user_id=167293545, output_dir="./downloads")
```

## Progress Tracking

### Features
- Progress bar for overall posts
- Progress bar for images per post
- ETA calculation
- Download speed metrics
- Summary report at end:
  - Total posts processed
  - Total images downloaded
  - Failed downloads
  - Total size downloaded
  - Time taken

## Advanced Features (Optional)

### Phase 2 Enhancements
1. **Multi-threading**: Download multiple images simultaneously
2. **Database**: SQLite to track download state
3. **GUI**: Simple Tkinter or web-based interface
4. **Scheduling**: Periodic checks for new posts
5. **Filters**: Download only certain file types or date ranges
6. **Metadata**: Save post descriptions, dates, etc. to JSON
7. **Duplicate Detection**: Use image hashing to avoid duplicates
8. **Incremental Updates**: Only download new posts since last run

## Testing Strategy

### Unit Tests
- URL parsing functions
- File naming sanitization
- Directory creation logic

### Integration Tests
- Full download workflow with test user
- Pagination handling
- Error recovery

### Manual Testing
- Test with various user IDs
- Test with users having different post counts
- Test interruption and resume
- Test rate limiting responses

## Legal & Ethical Considerations

⚠️ **Important Notes:**
1. Check kemono.cr's Terms of Service
2. Respect robots.txt file
3. Implement rate limiting to avoid server overload
4. Consider copyright of downloaded content
5. Personal use vs distribution considerations
6. May need to handle DMCA/takedown notices

## Development Phases

### Phase 1: MVP (Minimum Viable Product)
- [ ] Basic scraping for single user
- [ ] Download images from posts
- [ ] Create folder structure
- [ ] Simple error handling

### Phase 2: Robustness
- [ ] Pagination support
- [ ] Resume capability
- [ ] Better error handling
- [ ] Logging system
- [ ] Progress tracking

### Phase 3: Polish
- [ ] CLI with arguments
- [ ] Configuration file
- [ ] Multi-threading
- [ ] Advanced features

## Estimated Timeline
- Phase 1 (MVP): 4-6 hours
- Phase 2 (Robustness): 3-4 hours
- Phase 3 (Polish): 2-3 hours
- Testing & Debugging: 2-3 hours
- **Total**: ~12-16 hours

## Next Steps
1. Set up Python virtual environment
2. Install required dependencies
3. Inspect kemono.cr site structure (DevTools)
4. Implement basic scraper for one post
5. Extend to all posts for a user
6. Add error handling and logging
7. Implement progress tracking
8. Test with real user IDs
9. Refactor and optimize
