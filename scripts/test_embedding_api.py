# scripts/test_embedding_api.py
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("--- Embedding models ---")
names = []
for m in client.models.list():
    if "embedContent" in (getattr(m, "supported_actions", None) or []):
        names.append(m.name)
        print(m.name)

if not names:
    raise SystemExit("Koi embedding model nahi mila")

# pehla model jiske naam mein 'embedding' ho, warna list ka pehla
model = next((n for n in names if "embedding" in n), names[0])
print(f"\n--- Testing {model} ---")
res = client.models.embed_content(
    model=model,
    contents=["Machine learning internship in Bangalore", "Frontend React internship"],
)
vecs = [e.values for e in res.embeddings]
print("Vectors:", len(vecs), "| Dimension:", len(vecs[0]))