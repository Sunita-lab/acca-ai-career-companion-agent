import json
import random
from pathlib import Path

from faker import Faker
from fpdf import FPDF

fake = Faker("en_IN")
Faker.seed(42)
random.seed(42)

OUT = Path("data/resumes")
OUT.mkdir(parents=True, exist_ok=True)

SKILLS = ["Python", "SQL", "Pandas", "NumPy", "Scikit-learn", "TensorFlow",
          "PyTorch", "FastAPI", "Flask", "Streamlit", "Git", "Docker",
          "React", "JavaScript", "Java", "C++", "Power BI", "Tableau", "NLP"]
DEGREES = [("B.Tech", "Computer Science"), ("B.Tech", "Information Technology"),
           ("BCA", "Computer Applications"), ("B.Sc", "Data Science"),
           ("MCA", "Computer Applications")]
ROLES = ["Data Analyst Intern", "Backend Developer Intern",
         "ML Intern", "Web Developer Intern"]
PROJECTS = [("Resume Screener", "Ranked resumes using TF-IDF and cosine similarity"),
            ("Sales Dashboard", "Built interactive dashboard for monthly sales"),
            ("Chatbot", "Created FAQ chatbot using Gemini API"),
            ("House Price Predictor", "Trained regression model on housing data"),
            ("Expense Tracker", "Web app with SQLite storage")]


def make_candidate():
    deg, field = random.choice(DEGREES)
    has_exp = random.random() < 0.6
    exp = []
    if has_exp:
        exp.append({
            "role": random.choice(ROLES),
            "company": fake.company(),
            "duration": f"{random.randint(2, 6)} months",
        })
    projs = random.sample(PROJECTS, k=random.randint(1, 3))
    return {
        "name": fake.name(),
        "email": fake.email(),
        "phone": fake.phone_number(),
        "skills": random.sample(SKILLS, k=random.randint(4, 9)),
        "education": [{
            "degree": deg, "field": field,
            "institute": fake.company() + " Institute of Technology",
            "year": random.randint(2025, 2028),
        }],
        "experience": exp,
        "projects": [{"title": t, "description": d} for t, d in projs],
    }


def write(pdf, x, w, text, size=10, bold=False):
    pdf.set_x(x)
    pdf.set_font("Helvetica", "B" if bold else "", size)
    pdf.multi_cell(w, 6, text, new_x="LEFT", new_y="NEXT")


def build_pdf(c, layout, path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(True, 15)
    edu = c["education"][0]
    edu_txt = f'{edu["degree"]} {edu["field"]}, {edu["institute"]} ({edu["year"]})'

    if layout == "single":
        write(pdf, 10, 190, c["name"], 18, True)
        write(pdf, 10, 190, f'{c["email"]} | {c["phone"]}')
        write(pdf, 10, 190, "SKILLS", 12, True)
        write(pdf, 10, 190, ", ".join(c["skills"]))
        write(pdf, 10, 190, "EDUCATION", 12, True)
        write(pdf, 10, 190, edu_txt)
        if c["experience"]:
            write(pdf, 10, 190, "EXPERIENCE", 12, True)
            for e in c["experience"]:
                write(pdf, 10, 190, f'{e["role"]}, {e["company"]} ({e["duration"]})')
        write(pdf, 10, 190, "PROJECTS", 12, True)
        for p in c["projects"]:
            write(pdf, 10, 190, f'- {p["title"]}: {p["description"]}')
    else:  # two columns
        write(pdf, 10, 190, c["name"], 18, True)
        top = pdf.get_y() + 4
        pdf.set_y(top)
        write(pdf, 10, 60, "CONTACT", 11, True)
        write(pdf, 10, 60, f'{c["email"]}\n{c["phone"]}')
        write(pdf, 10, 60, "SKILLS", 11, True)
        write(pdf, 10, 60, "\n".join(c["skills"]))
        write(pdf, 10, 60, "EDUCATION", 11, True)
        write(pdf, 10, 60, edu_txt)
        pdf.set_y(top)
        if c["experience"]:
            write(pdf, 75, 125, "Experience", 12, True)
            for e in c["experience"]:
                write(pdf, 75, 125, f'{e["role"]}\n{e["company"]} | {e["duration"]}')
        write(pdf, 75, 125, "Projects", 12, True)
        for p in c["projects"]:
            write(pdf, 75, 125, f'{p["title"]}\n{p["description"]}')
    pdf.output(str(path))


if __name__ == "__main__":
    N = 10
    for i in range(1, N + 1):
        c = make_candidate()
        layout = "single" if i % 2 else "two_col"
        stem = f"resume_{i:02d}"
        build_pdf(c, layout, OUT / f"{stem}.pdf")
        (OUT / f"{stem}.json").write_text(json.dumps(c, indent=2), encoding="utf-8")
    print(f"{N} resumes + ground-truth JSON ban created: {OUT}")