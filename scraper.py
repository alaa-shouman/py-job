import json
import sys
import urllib.parse
from typing import List, Optional, Dict, Any
import requests
from bs4 import BeautifulSoup
from jobspy import scrape_jobs
import pandas as pd
import numpy as np

# Valid countries according to python-jobspy
VALID_COUNTRIES = {
    "argentina", "australia", "austria", "bahrain", "bangladesh", "belgium", 
    "bulgaria", "brazil", "canada", "chile", "china", "colombia", "costa rica", 
    "croatia", "cyprus", "czech republic", "czechia", "denmark", "ecuador", 
    "egypt", "estonia", "finland", "france", "germany", "greece", "hong kong", 
    "hungary", "india", "indonesia", "ireland", "israel", "italy", "japan", 
    "kuwait", "latvia", "lithuania", "luxembourg", "malaysia", "malta", "mexico", 
    "morocco", "netherlands", "new zealand", "nigeria", "norway", "oman", 
    "pakistan", "panama", "peru", "philippines", "poland", "portugal", "qatar", 
    "romania", "saudi arabia", "singapore", "slovakia", "slovenia", "south africa", 
    "south korea", "spain", "sweden", "switzerland", "taiwan", "thailand", 
    "türkiye", "turkey", "ukraine", "united arab emirates", "uk", "united kingdom", 
    "usa", "us", "united states", "uruguay", "venezuela", "vietnam", "usa/ca", 
    "worldwide"
}

# Common location aliases
LOCATION_ALIASES = {
    "remote": "Remote",
    "worldwide": "Worldwide",
}

CUSTOM_SITES = [
    {
        "name": "dice",
        "url": "https://www.dice.com/jobs?filters.postedDate=THREE&filters.workplaceTypes=Remote&q={keyword}",
        "list_selector": "div[role=list]",
        "list_item_selector": "div[role=listitem]",
        "item_url": "a"
    },
    {
        "name": "WWR",
        "url": "https://weworkremotely.com/remote-jobs/search?term={keyword}&categories%5B%5D=2&categories%5B%5D=17&categories%5B%5D=18",
        "list_selector": "section#category-2 > article > ul",
        "list_item_selector": "li",
        "item_url": "a.listing-link--unlocked"
    },
    {
        "name": "remoteOk",
        "url": "https://remoteok.com/remote-{keyword}-jobs",
        "list_selector": "table#jobsboard > tbody",
        "list_item_selector": "tr.job",
        "item_url": "a.preventLink"
    },
    {
        "name": "meetfrank",
        "url": "https://meetfrank.com/fully-remote-software-engineering-jobs",
        "list_selector": "div.dg.di",
        "list_item_selector": "div.hY",
        "item_url": "a"
    },
    {
        "name": "workable",
        "url": "https://jobs.workable.com/search?location=Lebanon&day_range=7&query={keyword}",
        "list_selector": "ul.jobsList__list-container--2L__X",
        "list_item_selector": "li",
        "item_url": "a"
    },
    {
        "name": "remocate",
        "url": "https://www.remocate.app/",
        "list_selector": "div.jobs_section > div.padding-global > div.container-large > div.jobs_wr > div.w-dyn-list > div.board-list",
        "list_item_selector": "div.w-dyn-item",
        "item_url": "a"
    },
    {
        "name": "naukrigulf",
        "url": "https://www.naukrigulf.com/jobs-in-lebanon?keywords={keyword}",
        "list_selector": "div.srp-listing > div.tuple-wrap.opaque-true",
        "list_item_selector": "div.ng-box.srp-tuple",
        "item_url": "a"
    },
    {
        "name": "bayt",
        "url": "https://www.bayt.com/en/lebanon/jobs/jobs-in-beirut/?q={keyword}",
        "list_selector": "div#results_inner_card > ul",
        "list_item_selector": "li",
        "item_url": "a"
    },
    {
        "name": "hire lebanese",
        "url": "https://www.hirelebanese.com/searchresults.aspx?order=date&keywords={keyword}&category=10&country=117,241,258,259,260",
        "list_selector": "table.ListBorder",
        "list_item_selector": "tr > td > div.panel > div.panel-heading",
        "item_url": "div.panel-title > h4 > a"
    }
]


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
    # if location_lower in VALID_COUNTRIES:
    #     return True, location
    
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


def fetch_description(url: str) -> Optional[str]:
    """
    Fetch job description from a URL if missing.
    """
    if not url:
        return None
        
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try common description containers
            # LinkedIn public job page
            desc = soup.find('div', {'class': 'show-more-less-html__markup'})
            if desc:
                return desc.get_text(strip=True)
                
            # Generic fallback: look for common description classes or just return body text
            for class_name in ['job-description', 'description', 'details', 'content']:
                desc = soup.find(class_=lambda x: x and class_name in x.lower())
                if desc:
                    return desc.get_text(strip=True)
            
            return None
    except Exception as e:
        print(f"Error fetching description for {url}: {e}", file=sys.stderr)
        return None


def scrape_custom_sites(keyword: str) -> List[Dict[str, Any]]:
    """
    Scrape jobs from custom sites defined in CUSTOM_SITES.
    """
    all_jobs = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    for site in CUSTOM_SITES:
        try:
            # Format URL with keyword if placeholder exists, otherwise use as is
            url = site["url"]
            if "{keyword}" in url:
                url = url.format(keyword=urllib.parse.quote(keyword))
            
            print(f"Scraping {site['name']}: {url}", file=sys.stderr)
            
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"Failed to fetch {site['name']}: {response.status_code}", file=sys.stderr)
                continue
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find list container
            if site.get("list_selector"):
                container = soup.select_one(site["list_selector"])
                if not container:
                    # Try searching in the whole document if list selector fails
                    container = soup
            else:
                container = soup
                
            # Find items
            items = container.select(site["list_item_selector"])
            print(f"Found {len(items)} items on {site['name']}", file=sys.stderr)
            
            for item in items:
                try:
                    # Extract link
                    link_elem = item.select_one(site["item_url"])
                    if not link_elem:
                        continue
                        
                    job_url = link_elem.get('href')
                    if job_url and not job_url.startswith('http'):
                        # Handle relative URLs
                        base_url = "/".join(url.split('/')[:3])
                        if job_url.startswith('/'):
                            job_url = base_url + job_url
                        else:
                            job_url = base_url + '/' + job_url
                            
                    title = link_elem.get_text(strip=True)
                    
                    # Basic job object
                    job = {
                        "site": site["name"],
                        "title": title,
                        "job_url": job_url,
                        "company": "Unknown", # Hard to extract generically without more selectors
                        "location": "Remote", # Defaulting to Remote as per context
                        "description": None
                    }
                    
                    # Try to find company/location if possible (heuristic)
                    # This is very rough and might need site-specific tuning
                    text_content = item.get_text(" | ", strip=True)
                    job["raw_text"] = text_content
                    
                    all_jobs.append(job)
                    
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error scraping {site['name']}: {e}", file=sys.stderr)
            continue
            
    return all_jobs


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
        # Scrape custom sites first
        custom_jobs = scrape_custom_sites(keyword)
        all_jobs.extend(custom_jobs)
        
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
                
                # Fix missing descriptions (especially for LinkedIn)
                for job in jobs_list:
                    if not job.get("description") and job.get("job_url"):
                        # Only fetch if it's LinkedIn or if description is strictly required
                        if "linkedin" in str(job.get("site", "")).lower():
                            print(f"Fetching missing description for {job.get('title')}...", file=sys.stderr)
                            job["description"] = fetch_description(job["job_url"])
                
                all_jobs.extend(jobs_list)
                print(f"Found {len(jobs_list)} jobs for '{keyword}' via jobspy", file=sys.stderr)
            else:
                print(f"No jobs found for '{keyword}' via jobspy", file=sys.stderr)
        
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
