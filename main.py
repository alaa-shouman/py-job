from fastapi import FastAPI
from scraper import scrape_jobs_by_keyword
import uvicorn

app = FastAPI(
    title="Job Scraper API",
    description="API for scraping job listings from LinkedIn and Indeed",
    version="1.0.0"
)


@app.get("/scrape")
def fetch_jobs(keywords: str = "Software Engineer", location: str = "Remote", results: int = 50, hours_old: int = 24):
    """
    Scrape jobs from LinkedIn and Indeed.
    
    Parameters:
    - keywords: Comma-separated job keywords (e.g., "Software Engineer,Python Developer")
    - location: Job location filter (default: "Remote")
    - results: Number of results per keyword (default: 50)
    - hours_old: Filter jobs posted within this many hours (default: 24)
    
    Returns: JSON with scraped jobs and metadata
    """
    # Parse keywords
    keywords_list = [k.strip() for k in keywords.split(",")]
    
    # Call the scraper
    result = scrape_jobs_by_keyword(
        keywords=keywords_list,
        location=location,
        results_wanted=results,
        hours_old=hours_old
    )
    
    return result


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    