# src/rag/chunking.py
def chunk_job(job: dict) -> list[dict]:
    head = f"{job['title']} at {job['company']} ({job['location']})"
    chunks = []

    chunks.append(("overview",
        f"{head}\nDomain: {job.get('domain', '')}\n"
        f"Duration: {job.get('duration', '')} | Stipend: {job.get('stipend', '')}\n"
        f"{job['description']}"))

    if job.get("responsibilities"):
        chunks.append(("responsibilities",
            f"{head}\nResponsibilities:\n- " + "\n- ".join(job["responsibilities"])))

    skills = f"{head}\nRequired skills: {', '.join(job['required_skills'])}\n"
    if job.get("preferred_skills"):
        skills += f"Preferred skills: {', '.join(job['preferred_skills'])}\n"
    if job.get("qualifications"):
        skills += f"Qualifications: {'; '.join(job['qualifications'])}\n"
    skills += (f"Experience: {job.get('experience_required', '')}\n"
               f"Education: {job.get('education_required', '')}")
    chunks.append(("skills", skills))

    return [
        {
            "id": f"{job['job_id']}::{ctype}",
            "text": text,
            "metadata": {
                "job_id": job["job_id"],
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "domain": job.get("domain", ""),
                "chunk_type": ctype,
            },
        }
        for ctype, text in chunks
    ]