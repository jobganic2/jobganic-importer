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

# Inference helpers
def normalize_employment_type(text):
    text = text.lower()
    if "remote" in text:
        return "Remote"
    if "hybrid" in text:
        return "Hybrid"
    if "on-site" in text or "onsite" in text:
        return "On-site"
    return None

def normalize_job_type(text):
    text = text.lower()
    if "intern" in text:
        return "Internship"
    if "part-time" in text or "part time" in text:
        return "Part-Time"
    if "full-time" in text or "full time" in text:
        return "Full-Time"
    return None

def normalize_experience_level(text):
    text = text.lower()
    if "entry" in text or "junior" in text:
        return "Entry"
    if "mid" in text or "intermediate" in text:
        return "Mid"
    if "senior" in text or "lead" in text:
        return "Senior"
    return None

def make_job_payload(job, company_name):
    job_id = job["id"]
    title = job.get("title", "")
    content = job.get("content", "")

    employment_type = job.get("employment_type") or normalize_employment_type(f"{title} {content}")
    job_type = job.get("job_type") or normalize_job_type(f"{title} {content}")
    experience_level = job.get("experience_level") or normalize_experience_level(f"{title} {content}")

    return {
        "id": str(job_id),
        "title": title,
        "company": company_name,
        "location": job["location"]["name"],
        "description": clean_description(content),
        "url": job["absolute_url"],
        "date_posted": job["updated_at"][:10],
        "source": "greenhouse",
        "department": job.get("department", {}).get("name"),
        "employment_type": employment_type,
        "job_type": job_type,
        "experience_level": experience_level
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
