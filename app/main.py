"""ACCA Streamlit app: student profile creation + resume upload."""
import sys
from pathlib import Path

# make `src` importable when running `streamlit run app/main.py` from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from src.db import init_db, create_student, save_resume, list_students
from src.resume_parser.extract_text import extract_text_from_pdf

UPLOAD_DIR = Path("data") / "uploads"

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
        student_id = create_student(name.strip(), email.strip(), phone.strip())
        saved_path = UPLOAD_DIR / f"{student_id}_{resume.name}"
        saved_path.write_bytes(resume.getvalue())
        save_resume(student_id, resume.name, str(saved_path), text)
        st.success(f"Profile saved (student id: {student_id}).")
        with st.expander("Extracted resume text (preview)"):
            st.text(text[:3000])

st.divider()
st.subheader("Saved profiles")
rows = list_students()
if rows:
    st.table([dict(r) for r in rows])
else:
    st.info("No profiles yet.")