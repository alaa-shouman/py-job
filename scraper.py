import json
import sys
from typing import List, Optional
from jobspy import scrape_jobs
import pandas as pd
import numpy as np

# Valid countries according to python-jobspy - filtered for high salary countries accessible to Lebanese citizens
VALID_COUNTRIES = {
    "australia", "austria", "bahrain", "belgium", "canada", "denmark", "finland", 
    "france", "germany", "hong kong", "ireland", "japan", "kuwait", "lebanon", 
    "luxembourg", "netherlands", "new zealand", "norway", "oman", "qatar", 
    "saudi arabia", "singapore", "south korea", "sweden", "switzerland", "taiwan", 
    "uk", "united kingdom", "usa", "us", "united states", "united arab emirates", 
    "worldwide"
}

# Common location aliases
LOCATION_ALIASES = {
    "remote": "Remote",
    "worldwide": "Worldwide",
}


def validate_location(location: str) -> tuple[bool, str]:
    """
    Validate if location is supported by jobspy.
    Returns (is_valid, normalized_location)
    """
    location_lower = location.lower().strip()
    
    # Check if it's a special case (Remote, Worldwide)
    if location_lower in ["remote", "worldwide"]:
        return True, location_lower.capitalize()
    
    # Check against valid countries
    if location_lower in VALID_COUNTRIES:
        return True, location
    
    return False, location


def clean_nan_values(data):
    """
    Recursively clean NaN and inf values from data structures.
    Converts them to None (which JSON can handle).
    """
    if isinstance(data, dict):
        return {key: clean_nan_values(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [clean_nan_values(item) for item in data]
    elif isinstance(data, float):
        if np.isnan(data) or np.isinf(data):
            return None
        return data
    elif pd.isna(data):
        return None
    return data


def scrape_jobs_by_keyword(
    keywords: List[str],
    location: str = "Remote",
    results_wanted: int = 50,
    hours_old: int = 24,
    site_names: Optional[List[str]] = None
) -> dict:

    
    if site_names is None:
        site_names = ["linkedin", "indeed","glassdoor", "zip_recruiter", "google"]
    
    # Validate location
    is_valid, normalized_location = validate_location(location)
    if not is_valid:
        return {
            "status": "error",
            "error": f"Invalid location: '{location}'",
            "message": f"'{location}' is not a supported location. Valid locations include: {', '.join(sorted(list(VALID_COUNTRIES)[:20]))}... and more",
            "valid_locations": sorted(list(VALID_COUNTRIES)),
            "total_jobs": 0,
            "keywords": keywords,
            "location": location,
            "jobs": []
        }
    
    all_jobs = []
    
    for keyword in keywords:
        try:
            print(f"Scraping jobs for keyword: {keyword}", file=sys.stderr)
            
            jobs_df = scrape_jobs(
                site_name=site_names,
                search_term=keyword,
                location=normalized_location,
                results_wanted=results_wanted,
                hours_old=hours_old
            )
            
            if not jobs_df.empty:
                # Fill NaN values with None before converting to dict
                jobs_df = jobs_df.where(pd.notna(jobs_df), None)
                
                # Convert DataFrame to list of dictionaries
                jobs_list = jobs_df.to_dict(orient="records")
                
                # Clean any remaining NaN values
                jobs_list = [clean_nan_values(job) for job in jobs_list]
                
                all_jobs.extend(jobs_list)
                print(f"Found {len(jobs_list)} jobs for '{keyword}'", file=sys.stderr)
            else:
                print(f"No jobs found for '{keyword}'", file=sys.stderr)
        
        except ValueError as e:
            error_msg = str(e)
            if "Invalid country" in error_msg or "Valid countries" in error_msg:
                print(f"Error scraping jobs for '{keyword}': Invalid location '{normalized_location}'", file=sys.stderr)
            else:
                print(f"Error scraping jobs for '{keyword}': {error_msg}", file=sys.stderr)
            continue
        except Exception as e:
            print(f"Error scraping jobs for '{keyword}': {str(e)}", file=sys.stderr)
            continue
    
    # Final cleanup of the entire response
    response = {
        "status": "success" if all_jobs else "no_results",
        "total_jobs": len(all_jobs),
        "keywords": keywords,
        "location": normalized_location,
        "jobs": all_jobs
    }
    
    return clean_nan_values(response)


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
        print("\nValid countries: Remote, USA, Canada, UK, etc.", file=sys.stderr)
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
