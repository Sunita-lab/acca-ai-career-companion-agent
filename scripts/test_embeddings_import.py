# scripts/test_embeddings_import.py
import importlib

def try_import(name):
    try:
        importlib.import_module(name)
        print(f"OK    {name}")
        return True
    except Exception as e:
        print(f"FAIL  {name} -> {type(e).__name__}: {e}")
        return False

print("--- Core ---")
try_import("numpy")

print("--- Local embedding options ---")
try_import("torch")
try_import("sentence_transformers")
try_import("faiss")
try_import("chromadb")

print("--- Gemini embedding API ---")
try:
    from google import genai
    print("OK    google.genai")
except Exception as e:
    print(f"FAIL  google.genai -> {type(e).__name__}: {e}")