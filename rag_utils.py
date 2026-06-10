import re
import os
from typing import List, Tuple

from guards.rag_policy import (
    RAG_SYSTEM_PROMPT,
    sanitize_retrieved_content,
    validate_generated_answer,
    validate_user_question,
)


def hybrid_retrieve(question: str, vectorstore, bm25, all_docs, top_k: int = 8) -> List:

    from rank_bm25 import BM25Okapi

    dense_hits = vectorstore.similarity_search(question, k=top_k)
    tokens = question.lower().split()
    bm25_scores = bm25.get_scores(tokens)
    top_bm25_idx = sorted(
        range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True
    )[:top_k]
    bm25_hits = [all_docs[i] for i in top_bm25_idx]
    merged = {d.page_content: d for d in dense_hits}
    for d in bm25_hits:
        merged.setdefault(d.page_content, d)
    dense_rank = {d.page_content: i for i, d in enumerate(dense_hits)}
    bm25_rank = {all_docs[i].page_content: i for i in top_bm25_idx}

    def rrf_score(text):
        dr = dense_rank.get(text, 9999)
        br = bm25_rank.get(text, 9999)
        return 1 / (60 + dr) + 1 / (60 + br)

    ranked = sorted(
        merged.values(), key=lambda d: rrf_score(d.page_content), reverse=True
    )
    return ranked[:top_k]


def get_answer(
    question: str, vectorstore, bm25, all_docs, chat_history: List[dict], top_k: int = 8
):

    from groq import Groq

    question_guard = validate_user_question(question)
    if not question_guard.passed:
        return question_guard.sanitized_text, [], ""

    hits = hybrid_retrieve(question, vectorstore, bm25, all_docs, top_k)
    if not hits:
        return "No relevant content found in your PDFs.", [], ""
    sources, ctx_parts = [], []
    for doc in hits:
        src = doc.metadata.get("source_file", "unknown")
        page = doc.metadata.get("page", "?")
        safe_content, _ = sanitize_retrieved_content(doc.page_content)
        ctx_parts.append(f"[File: {src} | Page: {page}]\n{safe_content}")
        sources.append({"file": src, "page": page})
    context = "\n\n---\n\n".join(ctx_parts)
    messages = [{"role": "system", "content": RAG_SYSTEM_PROMPT}]
    for entry in chat_history[-4:]:
        messages.append({"role": entry["role"], "content": entry["content"]})
    messages.append(
        {
            "role": "user",
            "content": f"DOCUMENT CONTEXT:\n{context}\n\nQUESTION: {question}\n\nAnswer based strictly on the context above:",
        }
    )
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    for model in ["llama-3.3-70b-versatile", "llama3-70b-8192", "mixtral-8b-32768"]:
        try:
            resp = client.chat.completions.create(
                model=model, messages=messages, temperature=0, max_tokens=100
            )
            answer = resp.choices[0].message.content.strip()
            answer_guard = validate_generated_answer(answer)
            if not answer_guard.passed:
                return answer_guard.sanitized_text, sources, context
            return answer, sources, context
        except Exception as e:
            if any(
                x in str(e)
                for x in ["decommissioned", "model_not_found", "404", "not found"]
            ):
                continue
            raise
    raise Exception("All models failed.")
