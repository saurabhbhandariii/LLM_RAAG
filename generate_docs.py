import os
from fpdf import FPDF

# Documentation mapping
file_explanations = {
    "app.py": (
        "Main Streamlit Application Entry Point",
        "app.py sets up the Streamlit UI, handles file uploads, manages session state, and coordinates the entire RAG pipeline.\n"
        "- Lines 1-56: Dummy Streamlit fallback for testing without UI.\n"
        "- Lines 57-83: Imports and Environment Setup (loads API keys, sets GROQ_MODELS).\n"
        "- Lines 85-190: Streamlit Page Config & Custom CSS styling to provide a dark, modern look.\n"
        "- Lines 192-200: Session State Initialization (vectorstore, chat_history, etc).\n"
        "- Lines 202-212: `get_embeddings()`: Initializes HuggingFace embeddings for dense retrieval.\n"
        "- Lines 214-223: `make_splitter()`: Configures RecursiveCharacterTextSplitter for document chunking.\n"
        "- Lines 225-260: `process_pdfs()`: Reads uploaded PDFs, redacts PII/secrets via `pdf_redactor`, splits into chunks, and builds FAISS and BM25 indexes.\n"
        "- Lines 262-279: `hybrid_retrieve()`: Implementation of Hybrid Retrieval (FAISS + BM25) combined via Reciprocal Rank Fusion (RRF).\n"
        "- Lines 281-289: `build_messages()`: Formats the system prompt, chat history, and context into a conversation array for the LLM.\n"
        "- Lines 291-374: `evaluate_response()`: Integrates DeepEval metrics (relevancy, hallucination) using Ollama, with fallback heuristics.\n"
        "- Lines 376-407: `get_answer()`: Invokes the Groq LLM across multiple models for redundancy.\n"
        "- Lines 410-454: Sidebar UI for uploading PDFs and clearing chat history.\n"
        "- Lines 456-525: Main Chat UI loop. It captures user input, runs `safe_rag_query` to fetch the sanitized answer securely, and displays the bot's response along with source citations.",
    ),
    "secure_rag.py": (
        "Secure RAG Pipeline Coordinator",
        "This file orchestrates the security guardrails wrapping the LLM call.\n"
        "- Lines 1-15: Imports guard layers (LLMGuardLayer, OllamaGuardLayer, GuardrailsLayer, TruffleHogLayer).\n"
        "- Lines 17-21: `run_sync()`: A helper to run synchronous functions inside the asyncio thread pool.\n"
        "- Lines 23-32: `_retrieve_chunks()`: Wraps the hybrid retrieval function.\n"
        "- Lines 34-44: `_scan_chunks()`: Scans all retrieved document chunks for prompt injections to prevent indirect attacks.\n"
        "- Lines 46-60: `_call_llm()`: Wrapper for the actual LLM completion.\n"
        "- Lines 62-115: `safe_rag_query()`: The core secured flow. It scans input using TruffleHog & LLM-Guard, retrieves chunks, scans chunks for injection, formats the prompt, fetches the answer, and finally scans the output using LLM-Guard, TruffleHog, and Guardrails.ai before returning the safe string.",
    ),
    "guards/trufflehog_layer.py": (
        "TruffleHog Secret Detection Layer",
        "This layer replaces the LLM-Guard Secrets scanner to detect API keys and credentials.\n"
        "- Lines 1-13: `TruffleHogLayer` class initialization.\n"
        "- Lines 15-49: `scan_text()`: Writes text to a temp file and invokes the TruffleHog3 CLI subprocess. If TruffleHog exits with code 2 and outputs JSON, it parses the secrets found and blocks the request.\n"
        "- Lines 51-55: Input/Output specific async wrappers (`scan_input`, `scan_output`).",
    ),
    "guards/llm_guard_layer.py": (
        "LLM-Guard Security Layer",
        "Configures the local LLM-Guard scanners for PII, Toxicity, and Prompt Injection.\n"
        "- Lines 1-14: Imports necessary scanners from the `llm_guard` package (fallback to None if unavailable).\n"
        "- Lines 16-48: `__init__()`: Sets up `input_scanners` (PromptInjection, BanTopics, Toxicity, Anonymize) and `output_scanners` (OutputToxicity, Sensitive, OutputBanTopics). The Sensitive scanner is explicitly configured with 'DATE_TIME' to catch DOBs.\n"
        "- Lines 50-71: `_run_scanner()`: Executes the scanner synchronously in a thread pool. It handles signature checking to pass the 'prompt' correctly to output scanners.\n"
        "- Lines 73-94: `scan_input()` / `scan_output()`: Iterates through all registered scanners. If any scanner fails, it aborts the process and logs the violation.",
    ),
    "guards/ollama_guard_layer.py": (
        "Ollama Llama-Guard-3 Layer",
        "Provides secondary safety checks using an Ollama-hosted model.\n"
        "- Lines 1-21: Attempts to import `ollama_guard`.\n"
        "- Lines 23-39: `_run_guard()`: Synchronous thread-pool execution of `self.guard.check(text)`. Returns whether the text is unsafe.\n"
        "- Lines 41-47: `scan_input()`: Uses the guard to block inappropriate questions or prompt injections before they reach the main LLM.",
    ),
    "guards/guardrails_layer.py": (
        "Guardrails AI Layer",
        "Validates the LLM output using specific structured expectations.\n"
        "- Lines 1-17: Imports Guardrails and specific validators (CompetitorCheck, ToxicLanguage).\n"
        "- Lines 19-27: Sets up the Guard object with the rules.\n"
        "- Lines 29-41: `_run_guard()`: Parses the LLM output against the guardrails rules.\n"
        "- Lines 43-49: `validate()`: Async wrapper. Returns the fallback message if validation fails.",
    ),
    "rag_utils.py": (
        "Core RAG Algorithms",
        "Contains the isolated logic for Hybrid Retrieval and LLM interaction, decoupled from Streamlit.\n"
        "- Lines 1-26: `hybrid_retrieve()`: Executes FAISS semantic search and BM25 sparse keyword search, computing scores using Reciprocal Rank Fusion (RRF = 1/(60+rank)).\n"
        "- Lines 28-76: `get_answer()`: Uses `hybrid_retrieve` to get chunks, formats a context string with source files/pages, builds the OpenAI-compatible message array with conversation history, and invokes the Groq client with a fallback model chain (llama3-70b-8192 -> mixtral-8b -> etc).",
    ),
    "guard_utils.py": (
        "Legacy Security Utils",
        "Contains the old heuristic security methods (fallback if advanced layers fail).\n"
        "- Lines 1-21: Configures legacy static lists and basic LLM-Guard checks (now superseded by the OOP `guards/` module).\n"
        "- Lines 23-28: `_BLACKLIST_PATTERN`: A regex blocking specific violent terms (weapons, knives, etc).\n"
        "- Lines 30-68: `check_prompt()` and `check_response()` functions using the old implementation.",
    ),
    "pdf_redactor.py": (
        "PDF PII Redaction",
        "Sanitizes PDF text immediately after loading to prevent PII ingestion.\n"
        "- Lines 1-13: Imports PyMuPDF (`fitz`) and defines static regexes for Email, Phone, Credit Cards, and Addresses.\n"
        "- Lines 15-28: `redact_text()`: Uses `re.sub` to replace matched PII patterns with `[REDACTED_EMAIL]`, `[REDACTED_PHONE]`, etc.\n"
        "- Lines 30-41: `extract_and_redact()`: Helper that extracts raw text from PDF pages and runs `redact_text` over each chunk.",
    ),
    "security.py": (
        "General Sanitization Utils",
        "Legacy module for basic string sanitization and masking.\n"
        "- Lines 1-7: Regex patterns for API keys and passwords.\n"
        "- Lines 9-35: `sanitize_text()`: Obfuscates passwords, emails (showing only first character), and phone numbers (masking all but last 4 digits).",
    ),
}


class PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 15)
        self.cell(
            0,
            10,
            "Multi-PDF RAG Application - Architecture & Codebase Explanation",
            0,
            new_x="LMARGIN",
            new_y="NEXT",
            align="C",
        )
        self.ln(5)

    def chapter_title(self, filename, title):
        self.set_font("Helvetica", "B", 12)
        self.set_fill_color(200, 220, 255)
        self.cell(
            0,
            10,
            f"File: {filename} - {title}",
            0,
            new_x="LMARGIN",
            new_y="NEXT",
            align="L",
            fill=True,
        )
        self.ln(4)

    def chapter_body(self, explanation, code):
        explanation = explanation.encode("latin-1", "replace").decode("latin-1")
        code = code.encode("latin-1", "replace").decode("latin-1")

        self.set_font("Helvetica", "", 11)
        self.multi_cell(0, 6, explanation)
        self.ln(4)

        # Code block
        self.set_font("Courier", "", 8)
        self.set_fill_color(240, 240, 240)
        self.multi_cell(0, 5, code, fill=True)
        self.ln()


def main():
    pdf = PDF()
    pdf.add_page()

    for filename, (title, explanation) in file_explanations.items():
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                code = f.read()

            if len(code) > 25000:
                code = code[:25000] + "\n... [Code Truncated for PDF]"

            pdf.chapter_title(filename, title)
            pdf.chapter_body(explanation, code)
        else:
            print(f"Warning: {filename} not found.")

    output_path = "Codebase_Explanation.pdf"
    pdf.output(output_path)
    print(f"PDF generated successfully at {output_path}")


if __name__ == "__main__":
    main()
