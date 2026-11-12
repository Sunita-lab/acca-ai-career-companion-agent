"""Quick check that your Gemini API key and model name work."""
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

client = genai.Client(api_key=api_key)
response = client.models.generate_content(
    model=model,
    contents="Reply with one short sentence: Gemini is working.",
)
print(response.text)