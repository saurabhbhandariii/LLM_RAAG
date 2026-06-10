import asyncio
import os
from dotenv import load_dotenv
from typing import List, Tuple
from guards.base import GuardResult, log_violation
from guards.llm_guard_layer import LLMGuardLayer
from guards.ollama_guard_layer import OllamaGuardLayer
from guards.guardrails_layer import GuardrailsLayer
from guards.trufflehog_layer import TruffleHogLayer
from guards.rag_policy import (
    sanitize_retrieved_content,
    validate_generated_answer,
    validate_user_question,
)

load_dotenv()

_llm_guard = LLMGuardLayer()
_ollama_guard = OllamaGuardLayer()
_trufflehog = TruffleHogLayer()
_guardrails = GuardrailsLayer(
    fallback_msg=os.getenv("GUARD_FALLBACK_MSG", "Sorry, I can't answer that.")
)


async def run_sync(fn, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))


async def _retrieve_chunks(
    question: str, vectorstore, bm25, all_docs, top_k: int = 8
) -> List[Tuple[str, dict]]:
    from rag_utils import hybrid_retrieve

    hits = await run_sync(hybrid_retrieve, question, vectorstore, bm25, all_docs, top_k)
    return [(hit.page_content, hit.metadata) for hit in hits]


async def _scan_chunks(chunks: List[Tuple[str, dict]]) -> GuardResult:

    for text, _ in chunks:
        _, changed = sanitize_retrieved_content(text)
        if changed:
            log_violation(
                category="RetrievedInstructionOrProtectedData",
                scanner_name="RAGPolicyChunk",
                input_text=text,
            )
            continue
        result = await _llm_guard.scan_input(text)
        if not result.passed:
            log_violation(
                category="ChunkInjection", scanner_name="LLMGuardChunk", input_text=text
            )
            return GuardResult(
                passed=False, blocked_by="LLMGuardChunk", reason=result.reason
            )
    return GuardResult(passed=True)


async def _call_llm(question: str, context: str, chat_history: List[dict]):

    from rag_utils import get_answer

    answer, sources, used_context = await run_sync(
        get_answer,
        question,
        None,
        None,
        None,
        [],
        top_k=8,
    )
    return answer, sources, used_context


async def safe_rag_query(user_input: str) -> GuardResult:

    result = validate_user_question(user_input)
    if not result.passed:
        return result

    # 1. TruffleHog input scanning
    result = await _trufflehog.scan_input(user_input)
    if not result.passed:
        return result

    # 2. LLM‑guard input scanning
    result = await _llm_guard.scan_input(user_input)
    if not result.passed:
        return result

    result = await _ollama_guard.scan_input(user_input)
    if not result.passed:
        return result

    import streamlit as st

    vectorstore = st.session_state.get("vectorstore")
    bm25 = st.session_state.get("bm25")
    all_docs = st.session_state.get("all_docs")
    if not vectorstore or not bm25 or not all_docs:
        return GuardResult(passed=False, blocked_by="RAG", reason="Index not built")

    chunks = await _retrieve_chunks(user_input, vectorstore, bm25, all_docs)

    chunk_scan = await _scan_chunks(chunks)
    if not chunk_scan.passed:
        return chunk_scan

    context_parts = []
    for text, meta in chunks:
        src = meta.get("source_file", "unknown")
        page = meta.get("page", "?")
        safe_text, _ = sanitize_retrieved_content(text)
        context_parts.append(f"[File: {src} | Page: {page}]\n{safe_text}")
    context = "\n\n---\n\n".join(context_parts)

    from rag_utils import get_answer

    answer, sources, _ = await run_sync(
        get_answer,
        user_input,
        vectorstore,
        bm25,
        all_docs,
        st.session_state.get("chat_history", []),
        top_k=8,
    )

    result = await _llm_guard.scan_output(answer, prompt=user_input)
    if not result.passed:
        return result
    safe_answer = result.sanitized_text

    # 6.5 TruffleHog output scanning
    result = await _trufflehog.scan_output(safe_answer, prompt=user_input)
    if not result.passed:
        return result

    result = validate_generated_answer(safe_answer)
    if not result.passed:
        return result

    result = await _guardrails.validate(safe_answer)
    return result
