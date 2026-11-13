"""Extract raw text from an uploaded PDF resume."""
import pdfplumber


def extract_text_from_pdf(file) -> str:
    """Return all text from a PDF (path or file-like object).

    Returns an empty string if no text is found (e.g. scanned image PDFs).
    """
    pages = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages.append(text)
    return "\n".join(pages).strip()