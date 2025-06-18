import requests
import datetime
import os

print("🚀 Job Importer started...")

COMPANIES = {
    "bark": "Bark",
    "vitalfarms": "Vital Farms",
    "phxproduction": "The Honest Company",
    "sweetgreen": "Sweetgreen"
}

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

def fetch_jobs(token):
    url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()["jobs"]

def clean_description(html):
    return html.replace("\n", " ").replace("\r", " ").strip()

def make_job_payload(job, company_name):
    return {
        "id": str(job["id"]),
        "title": job["title"],
        "company": company_name,
        "location": job["location"]["name"],
        "description": clean_description(job["content"]),
        "url": job["absolute_url"],
        "date_posted": job["updated_at"][:10],
        "source": "greenhouse",
        "department": job.get("departments", [{}])[0].get("name") if job.get("departments") else None,
        "employment_type": job.get("metadata", [{}])[0].get("value") if "employment" in str(job.get("metadata", "")).lower() else None,
        "job_type": job.get("metadata", [{}])[1].get("value") if "job" in str(job.get("metadata", "")).lower() else None,
        "experience_level": next((item["value"] for item in job.get("metadata", []) if "experience" in item.get("name", "").lower()), None),
        "industry": next((item["value"] for item in job.get("metadata", []) if "industry" in item.get("name", "").lower()), None),
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
