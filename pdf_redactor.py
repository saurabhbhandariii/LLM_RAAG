import re
from typing import List

try:
    import fitz
except Exception:
    fitz = None

_EMAIL_REGEX = re.compile(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)")
_PHONE_REGEX = re.compile(r"(\+?\d{1,3}[\s-]?)?(\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4})")
_CARD_REGEX = re.compile(r"\b(?:\d[ -]*?){13,19}\b")  # simplistic card pattern
_CVV_REGEX = re.compile(r"\b\d{3,4}\b")
_ADDRESS_REGEX = re.compile(
    r"\b\d{1,5}\s+[A-Za-z0-9\.\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Way)\b",
    re.IGNORECASE,
)


def redact_text(text: str) -> str:

    text = _EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
    text = _PHONE_REGEX.sub("[REDACTED_PHONE]", text)
    text = _CARD_REGEX.sub("[REDACTED_CARD]", text)
    text = re.sub(
        r"(?i)(cvv|cvc|security code)[:\s]*\d{3,4}", r"\1: [REDACTED_CVV]", text
    )
    text = _ADDRESS_REGEX.sub("[REDACTED_ADDRESS]", text)
    return text


def extract_text_from_pdf(pdf_path: str) -> List[str]:

    if fitz is None:
        raise ImportError("PyMuPDF (fitz) is required for PDF extraction")
    doc = fitz.open(pdf_path)
    pages_text = []
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        page_text = page.get_text()
        pages_text.append(page_text)
    return pages_text


def extract_and_redact(pdf_path: str) -> List[str]:

    raw_chunks = extract_text_from_pdf(pdf_path)
    safe_chunks = [redact_text(chunk) for chunk in raw_chunks]
    return safe_chunks
