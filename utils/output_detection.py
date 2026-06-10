import re

def detect_output_type(question: str) -> str:
    """Return one of: 'text', 'table', 'chart', 'excel', 'docx', 'pdf', 'pptx'.
    Simple keyword‑based detection.
    """
    q = question.lower()
    if any(k in q for k in ["table", "comparison", "structured list", "tabular"]):
        return "table"
    if any(k in q for k in ["chart", "graph", "visualization", "trend", "statistics"]):
        return "chart"
    if any(k in q for k in ["excel", "spreadsheet", "sheet", "dataset", "export"]):
        return "excel"
    if any(k in q for k in ["docx", "document", "report", "proposal", "notes", "sop", "meeting"]):
        return "docx"
    if any(k in q for k in ["pdf", "printable", "invoice", "certificate", "formal report"]):
        return "pdf"
    if any(k in q for k in ["pptx", "slides", "presentation", "deck", "pitch"]):
        return "pptx"
    return "text"
