# src/rag/embed.py
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

EMBED_MODEL = os.getenv("EMBED_MODEL", "gemini-embedding-001")
EMBED_DIM = 768

_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def embed_texts(texts: list[str], task_type: str, batch_size: int = 25) -> list[list[float]]:
    """task_type: RETRIEVAL_DOCUMENT (for postings) or RETRIEVAL_QUERY (for search queries)."""
    out: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        for attempt in range(4):
            try:
                res = _client.models.embed_content(
                    model=EMBED_MODEL,
                    contents=batch,
                    config=types.EmbedContentConfig(
                        task_type=task_type, output_dimensionality=EMBED_DIM
                    ),
                )
                out.extend(e.values for e in res.embeddings)
                break
            except Exception as e:  # noqa: BLE001
                wait = 60
                print(f"   embed failed ({e}); retry in {wait}s")
                time.sleep(wait)
        else:
            raise RuntimeError("Embedding failed after 4 attempts")
        time.sleep(20)  # free-tier rate limit se bachne ke liye
    return out