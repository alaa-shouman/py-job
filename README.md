# Job Scraper Script

A Python script that scrapes job listings from LinkedIn and Indeed, returning clean JSON output for integration with n8n and other workflow tools.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Command-line Interface

```bash
python3 scraper.py "<keyword1>,<keyword2>" "<location>" [results] [hours_old]
```

**Examples:**

```bash
# Single keyword, remote jobs
python3 scraper.py "Software Engineer" "Remote"

# Multiple keywords
python3 scraper.py "Software Engineer,Python Developer" "Remote" 50 24

# With custom result count and time filter
python3 scraper.py "DevOps Engineer" "New York, NY" 100 48

# Default values
python3 scraper.py "Data Scientist" "San Francisco"
```

**Parameters:**
- `keyword1,keyword2` (required): Job search keywords separated by commas
- `location` (optional): Job location filter (default: "Remote")
- `results` (optional): Number of results per keyword (default: 50)
- `hours_old` (optional): Filter jobs posted within this many hours (default: 24)

### Python API

Use the `scraper.py` module directly in your Python code:

```python
from scraper import scrape_jobs_by_keyword

result = scrape_jobs_by_keyword(
    keywords=["Software Engineer", "Python Developer"],
    location="Remote",
    results_wanted=50,
    hours_old=24
)

print(result['total_jobs'])
print(result['jobs'])
```

## Output Format

The script returns JSON with the following structure:

```json
{
  "status": "success",
  "total_jobs": 9,
  "keywords": ["Software Engineer"],
  "location": "Remote",
  "jobs": [
    {
      "id": "in-49122834556e8af0",
      "site": "indeed",
      "job_url": "https://...",
      "title": "Senior Full Stack Developer",
      "company": "MicroVentures",
      "location": "Remote, US",
      "date_posted": "2025-12-27",
      "job_type": "fulltime",
      "description": "Full job description...",
      "is_remote": true,
      ...
    }
  ]
}
```

## n8n Integration

In n8n, use the HTTP Request node to call this script:

1. **Execute Command** node or
2. **SSH/Script** node

Configure with:
```
Command: python3 /path/to/scraper.py "Software Engineer,Python Developer" "Remote" 50 24
```

The JSON output can be directly consumed by subsequent nodes for:
- Sending to Gemini for job matching
- Filtering results
- Sending to Telegram
- Storing in databases

## Project Structure

```
py-job/
├── scraper.py           # Main scraping script
├── requirements.txt     # Python dependencies
├── main.py             # Optional FastAPI server (for HTTP API)
└── README.md           # This file
```

## Dependencies

- `jobspy` - Job scraping library
- `pandas` - Data processing
- `fastapi` - Optional web framework
- `uvicorn` - Optional web server
- `python-dotenv` - Environment variable management
- `requests` - HTTP requests

## Notes

- The script outputs to stdout for easy piping and integration
- Errors are printed to stderr to avoid JSON pollution
- Large job descriptions are included in full for Gemini analysis
- NaN values represent missing data from job sources
- LinkedIn and Indeed scraping may have rate limiting

## Workflow with n8n

1. **Scrape Jobs** → Run the Python script with your keywords
2. **Parse JSON** → Extract job data
3. **Send to Gemini** → Match jobs against your CV skills
4. **Filter Results** → Keep only high-match jobs
5. **Send to Telegram** → Deliver recommendations to your channel

## License

MIT
