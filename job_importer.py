
import requests
import datetime
import os

print("🚀 Job Importer started...")

# ✅ Greenhouse company tokens + display names
COMPANIES = {
    "bark": "Bark",
    "vitalfarms": "Vital Farms",
    "phxproduction": "The Honest Company",
    "sweetgreen": "Sweetgreen"
}

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

REQUIRED_FIELDS = ["id", "title", "company", "location", "description", "url", "date_posted", "source"]

def fetch_jobs(token):
    url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()["jobs"]

def clean_description(html):
    return html.replace("\n", " ").replace("\r", " ").strip()

def extract_metadata(metadata_list, key):
    if isinstance(metadata_list, list):
        for item in metadata_list:
            if item.get("name") == key:
                return item.get("value")
    return None

def make_job_payload(job, company_name):
    job_id = job["id"]
    location = job.get("location", {}).get("name", "")
    metadata = job.get("metadata", [])

    return {
        "id": str(job_id),
        "title": job["title"],
        "company": company_name,
        "location": location,
        "description": clean_description(job["content"]),
        "url": job["absolute_url"],
        "date_posted": job["updated_at"][:10],
        "source": "greenhouse",
        "department": job.get("department", {}).get("name"),
        "employment_type": extract_metadata(metadata, "Employment Type"),
        "job_type": extract_metadata(metadata, "Job Type"),
        "experience_level": extract_metadata(metadata, "Experience Level"),
        "industry": extract_metadata(metadata, "Industry"),
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
        try:
            print(f"📡 Fetching jobs for {company_name} ({token})...")
            jobs = fetch_jobs(token)
            print(f"📦 Found {len(jobs)} jobs at {company_name}")

            for job in jobs:
                job_payload = make_job_payload(job, company_name)
                post_to_supabase(job_payload)
        except Exception as e:
            print(f"❌ Error fetching jobs for {company_name} ({token}): {e}")

if __name__ == "__main__":
    main()
