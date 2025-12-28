import json
import sys
from typing import List, Optional
from jobspy import scrape_jobs
import pandas as pd


def scrape_jobs_by_keyword(
    keywords: List[str],
    location: str = "Remote",
    results_wanted: int = 50,
    hours_old: int = 24,
    site_names: Optional[List[str]] = None
) -> dict:
    """
    Scrape jobs from LinkedIn and Indeed based on keywords.
    
    Args:
        keywords: List of job keywords to search for (e.g., ["Software Engineer", "Python Developer"])
        location: Job location filter (default: "Remote")
        results_wanted: Number of results to fetch per keyword (default: 50)
        hours_old: Filter jobs posted within this many hours (default: 24)
        site_names: List of job sites to scrape (default: ["linkedin", "indeed"])
    
    Returns:
        dict: Contains jobs list with all job details, count, and metadata
    """
    
    if site_names is None:
        site_names = ["linkedin", "indeed"]
    
    all_jobs = []
    
    for keyword in keywords:
        try:
            print(f"Scraping jobs for keyword: {keyword}", file=sys.stderr)
            
            jobs_df = scrape_jobs(
                site_name=site_names,
                search_term=keyword,
                location=location,
                results_wanted=results_wanted,
                hours_old=hours_old
            )
            
            if not jobs_df.empty:
                # Convert DataFrame to list of dictionaries
                jobs_list = jobs_df.to_dict(orient="records")
                all_jobs.extend(jobs_list)
                print(f"Found {len(jobs_list)} jobs for '{keyword}'", file=sys.stderr)
            else:
                print(f"No jobs found for '{keyword}'", file=sys.stderr)
        
        except Exception as e:
            print(f"Error scraping jobs for '{keyword}': {str(e)}", file=sys.stderr)
            continue
    
    return {
        "status": "success" if all_jobs else "no_results",
        "total_jobs": len(all_jobs),
        "keywords": keywords,
        "location": location,
        "jobs": all_jobs
    }


def main():
    """
    Command-line interface for the job scraper.
    Usage: python scraper.py "<keyword1>,<keyword2>" "<location>" [results] [hours_old]
    
    Example:
        python scraper.py "Software Engineer,Python Developer" "Remote" 50 24
        python scraper.py "DevOps Engineer" "New York, NY"
    """
    
    if len(sys.argv) < 2:
        print("Usage: python scraper.py \"<keyword1>,<keyword2>\" \"<location>\" [results] [hours_old]", file=sys.stderr)
        sys.exit(1)
    
    # Parse command-line arguments
    keywords_str = sys.argv[1]
    location = sys.argv[2] if len(sys.argv) > 2 else "Remote"
    results_wanted = int(sys.argv[3]) if len(sys.argv) > 3 else 50
    hours_old = int(sys.argv[4]) if len(sys.argv) > 4 else 24
    
    # Split keywords by comma
    keywords = [k.strip() for k in keywords_str.split(",")]
    
    # Scrape jobs
    result = scrape_jobs_by_keyword(
        keywords=keywords,
        location=location,
        results_wanted=results_wanted,
        hours_old=hours_old
    )
    
    # Output as JSON to stdout
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
