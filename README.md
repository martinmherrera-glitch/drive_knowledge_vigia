# drive_knowledge_vigia
# Website Screenshot Scraper

A Python tool to automatically capture full-page screenshots from a list of website URLs and optionally upload them to Google Drive.

## Features

- ✅ Read URLs from Excel/CSV files
- ✅ Capture full-page screenshots (entire scrollable content)
- ✅ Headless browser operation (runs in background)
- ✅ Save screenshots locally
- ✅ Optional: Upload screenshots to Google Drive
- ✅ Progress tracking and error handling
- ✅ Results export to CSV

## Installation

1. Install required packages:

```bash
pip install -r requirements.txt
```

2. Make sure you have Chrome browser installed (ChromeDriver will be auto-downloaded)

## Quick Start

### Option 1: Simple Notebook (Easiest)

Open `Test.ipynb` and follow the examples. This is perfect for:
- Quick testing
- Learning how it works
- Simple screenshot capture without Drive upload

### Option 2: Full Featured Script

Use `website_screenshot_scraper.py` for:
- Batch processing many URLs
- Google Drive integration
- Production use

## Usage

### Basic Usage (Local Screenshots Only)

```python
from website_screenshot_scraper import WebsiteScreenshotScraper

# Initialize scraper
scraper = WebsiteScreenshotScraper(
    spreadsheet_path="links.xlsx"  # Your Excel/CSV file with URLs
)

# Run and capture screenshots
results = scraper.run(
    url_column='URL',  # Column name with URLs
    output_dir='screenshots',
    upload_to_drive=False
)
```

### With Google Drive Upload

1. **Setup Google Drive API:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable Google Drive API
   - Create credentials (Service Account)
   - Download JSON key file

2. **Run with Drive upload:**

```python
scraper = WebsiteScreenshotScraper(
    spreadsheet_path="links.xlsx",
    drive_folder_id="YOUR_DRIVE_FOLDER_ID",  # Optional: specific folder
    credentials_path="credentials.json"  # Path to your Google API key
)

results = scraper.run(upload_to_drive=True)
```

## Spreadsheet Format

Your Excel/CSV file should have URLs in a column. Example:

| URL |
|-----|
| https://www.example.com |
| https://www.python.org |
| https://www.github.com |

Or with additional columns:

| Name | URL | Category |
|------|-----|----------|
| Example | https://www.example.com | Demo |
| Python | https://www.python.org | Programming |

## Configuration Options

### WebsiteScreenshotScraper Parameters:

- `spreadsheet_path`: Path to your Excel/CSV file (required)
- `drive_folder_id`: Google Drive folder ID for uploads (optional)
- `credentials_path`: Path to Google API credentials JSON (optional)

### run() Method Parameters:

- `url_column`: Name of the column containing URLs (default: 'URL')
- `output_dir`: Directory to save screenshots (default: 'screenshots')
- `upload_to_drive`: Whether to upload to Google Drive (default: True)

## Output

The script creates:
1. **Screenshots folder**: PNG files of each webpage
2. **screenshot_results.csv**: Summary of all operations with:
   - URL
   - Filename
   - Local path
   - Success status
   - Drive ID (if uploaded)

## Tips

- **Large pages**: Some websites may take longer to load and capture
- **Wait time**: Adjust `time.sleep()` values if pages load slowly
- **Headless mode**: Remove `--headless` from Chrome options to see the browser
- **User agent**: Already configured to avoid bot detection
- **Rate limiting**: 2-second delay between requests (adjust as needed)

## Troubleshooting

### ChromeDriver issues:
- Make sure Chrome browser is installed
- Run with administrator privileges if needed
- Check your Chrome version matches ChromeDriver

### Google Drive upload fails:
- Verify credentials.json is valid
- Check folder ID is correct (optional parameter)
- Ensure API is enabled in Google Cloud Console

### Screenshots are incomplete:
- Increase wait time: `time.sleep(5)` instead of `time.sleep(3)`
- Some sites may have lazy loading - consider scrolling simulation

### Memory issues with many URLs:
- Process in batches
- Close browser between batches
- Clear screenshot folder periodically

## Advanced Features

### Custom Chrome Options:

```python
# In setup_driver() method, you can add:
chrome_options.add_argument('--window-size=1920,1080')
chrome_options.add_argument('--disable-images')  # Faster loading
```

### Filter URLs before processing:

```python
urls = scraper.read_urls()
urls = [url for url in urls if 'specific-domain' in url]
results = scraper.process_urls(urls)
```

## Examples

See `Test.ipynb` for interactive examples and testing.

## License

This is a utility script for personal/professional use. Respect website terms of service and robots.txt when scraping.
