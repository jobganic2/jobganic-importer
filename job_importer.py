import os
import requests
import hashlib
import datetime

# CONFIG — customize per company
COMPANIES = {
    "bark": "Bark",
    "patagonia": "Patagonia",
    "vitalfarms": "Vital Farms",
    "haincelestial": "Hain Celestial",
    "organicvalley": "Organic Valley",
    "seventhgeneration": "Seventh Generation"
}

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Required fields (match Supabase schema)
REQUIRED_FIELDS = ["id", "title", "company", "location", "description", "url", "date_posted", "source"]

def fetch_jobs():
    url = f"https://boards-api.greenhouse.io/v1/boards/{GREENHOUSE_BOARD_TOKEN}/jobs?content=true"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()["jobs"]

def clean_description(html):
    return html.replace("\n", " ").replace("\r", " ").strip()

def make_job_payload(job):
    job_id = job["id"]
    return {
        "id": str(job_id),
        "title": job["title"],
        "company": "Bark",
        "location": job["location"]["name"],
        "description": clean_description(job["content"]),
        "url": job["absolute_url"],
        "date_posted": job["updated_at"][:10],  # Format: YYYY-MM-DD
        "source": "greenhouse",
        "department": job.get("department", {}).get("name"),
    }

def post_to_supabase(job_data):
    url = f"{SUPABASE_URL}/rest/v1/jobs"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }
    response = requests.post(url, json=job_data, headers=headers)
    if not response.ok:
        print(f"❌ Failed to insert job {job_data['id']}: {response.status_code} {response.text}")
    else:
        print(f"✅ Inserted job {job_data['id']}")

def main():
    for token, company_name in COMPANIES.items():
        print(f"📡 Fetching jobs for {company_name} ({token})...")
        jobs = fetch_jobs(token)
        print(f"📦 Found {len(jobs)} jobs at {company_name}")

        for job in jobs:
            job_payload = make_job_payload(job, company_name)
            post_to_supabase(job_payload)
