# Kemono Downloader

Download all images from Kemono.cr user posts, organized into folders.

## Installation

1. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage
```bash
python main.py --user-id 167293545
```

### With Custom Output Directory
```bash
python main.py --user-id 167293545 --output ./my_downloads
```

### With Debug Logging
```bash
python main.py --user-id 167293545 --log-level DEBUG
```

### Re-download Existing Files
```bash
python main.py --user-id 167293545 --no-skip-existing
```

## Output Structure

```
downloads/
└── user_167293545/
    ├── post_148605353/
    │   ├── image_001.png
    │   ├── image_002.jpg
    │   └── ...
    ├── post_148605354/
    │   └── ...
    └── ...
```

## Features

- ✅ Recursive download of all posts for a user
- ✅ Automatic pagination handling
- ✅ Organized folder structure (user/post/images)
- ✅ **Async downloads with smart rate limiting** (no DDoS!)
- ✅ Skip already downloaded files
- ✅ Progress bars with ETA
- ✅ Retry logic for failed downloads
- ✅ Detailed logging
- ✅ Download statistics summary
- ✅ Selenium-based scraping (handles JavaScript)

## Configuration

Edit `config.py` to customize:
- Request delays and rate limiting
- Max concurrent downloads (default: 3)
- Batch size and pauses
- Retry attempts
- Download directory
- User agent
- And more...

## Troubleshooting

### No posts found
- Verify the user ID is correct
- Check if the user page is accessible in your browser

### Download failures
- Check your internet connection
- Try increasing `REQUEST_DELAY` in config.py
- Check if kemono.cr is accessible

### SSL errors
- Set `VERIFY_SSL = False` in config.py (not recommended for production)

## Legal Notice

This tool is for educational purposes. Please:
- Respect kemono.cr's Terms of Service
- Use reasonable rate limiting
- Consider copyright implications
- Use for personal purposes only

## License

MIT License - See LICENSE file for details
