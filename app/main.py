"""ACCA Streamlit app: student profile creation + resume upload."""
import sys
from pathlib import Path

# make `src` importable when running `streamlit run app/main.py` from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from src.db import (
    init_db, create_student, save_resume, list_students, save_profile,
    find_student_by_email, resume_exists,
)
from src.resume_parser.parse_resume import parse_resume
from src.resume_parser.extract_text import extract_text_from_pdf
from src.db import get_profile
from src.profile.schema import CandidateProfile
from src.matching.agent import match_profile

PROJECT_ROOT = Path(__file__).resolve().parent.parent
UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads"

init_db()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

st.title("ACCA: AI Career Companion Agent")
st.subheader("Create your profile")

with st.form("profile_form"):
    name = st.text_input("Full name")
    email = st.text_input("Email")
    phone = st.text_input("Phone (optional)")
    resume = st.file_uploader("Upload resume (PDF)", type=["pdf"])
    submitted = st.form_submit_button("Save profile")

if submitted:
    if not name.strip():
        st.error("Please enter your name.")
    elif resume is None:
        st.error("Please upload your resume as a PDF.")
    else:
        text = extract_text_from_pdf(resume)
        if not text:
            st.warning("No text found in this PDF. It may be a scanned image.")
        email_clean = email.strip()
        student_id = find_student_by_email(email_clean) or create_student(
            name.strip(), email_clean, phone.strip()
        )
        if resume_exists(student_id, text):
            st.info("This resume is already saved for this student, so it was not added again.")
        else:
            saved_path = UPLOAD_DIR / f"{student_id}_{resume.name}"
            saved_path.write_bytes(resume.getvalue())
            resume_id = save_resume(student_id, resume.name, str(saved_path), text)
            st.success(f"Profile saved (student id: {student_id}).")
            if text:
                with st.spinner("Parsing resume with Gemini..."):
                    try:
                        profile = parse_resume(text)
                        save_profile(student_id, resume_id, profile.model_dump_json())
                        st.success("Resume parsed into a structured profile.")
                        with st.expander("Parsed profile (JSON)"):
                            st.json(profile.model_dump())
                    except Exception as e:
                        st.error(f"Resume parsing failed: {e}")
        with st.expander("Extracted resume text (preview)"):
            st.text(text[:3000])

st.divider()
st.subheader("Saved profiles")
rows = list_students()
if rows:
    header = "| ID | Name | Email | Resume | Uploaded |\n|---|---|---|---|---|\n"
    body = "".join(
        f"| {r['id']} | {r['name']} | {r['email']} | {r['file_name']} | {r['uploaded_at']} |\n"
        for r in rows
    )
    st.markdown(header + body)
else:
    st.info("No profiles yet.")
st.divider()
st.subheader("Find matching internships")

# Create a dictionary of student names with their IDs as keys
student_names = {r["id"]: r["name"] for r in rows}

if not student_names:
    st.info("Save a profile first.")
else:
    chosen_id = st.selectbox(
        "Select student",
        options=list(student_names.keys()),
        format_func=lambda i: f"{i} - {student_names[i]}",
    )
    if st.button("Find matching internships"):
        saved = get_profile(chosen_id)
        if saved is None:
            st.warning("No parsed profile found for this student. Please upload and parse a resume first.")
        else:
            profile = CandidateProfile.model_validate_json(saved["profile_json"])
            with st.spinner("Finding matches(This may take a minute)..."):
                try:
                    st.session_state["match_results"] = (chosen_id, match_profile(profile, k=10))
                except Exception as e:
                    st.error(f"Matching failed: {e}")

    # results are kept in session state so they persist across reruns
    state = st.session_state.get("match_results")
    if state and state[0] == chosen_id:
        for rank, item in enumerate(state[1], 1):
            job, m = item["job"], item["match"]
            title = f"{rank}. {m.score}/100 | {job['title']} | {job['company']} | {job['location']}"
            with st.expander(title):
                st.markdown(f"**Matched skills:** {', '.join(m.matched_skills) or '-'}")
                st.markdown(f"**Missing skills:** {', '.join(m.missing_skills) or '-'}")
                st.markdown(f"**Why:** {m.reasoning}")
                st.caption(
                    f"{job['job_id']} | {job.get('duration', '')} | "
                    f"{job.get('stipend', '')} | retrieval score {item['job']['retrieval_score']}"
                )