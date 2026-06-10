from types import SimpleNamespace

try:
    import streamlit as st
except ModuleNotFoundError:

    class SessionState(dict):
        def __getattr__(self, name):
            return self.get(name)

        def __setattr__(self, name, value):
            self[name] = value

    class DummySt:
        session_state = SessionState()

        def set_page_config(self, *args, **kwargs):
            pass

        def markdown(self, *args, **kwargs):
            pass

        def caption(self, *args, **kwargs):
            pass

        def spinner(self, text):
            class _Spinner:
                def __enter__(self):
                    return None

                def __exit__(self, exc_type, exc, tb):
                    return False

            return _Spinner()

        def cache_resource(self, *args, **kwargs):
            def decorator(func):
                return func

            return decorator

        def subheader(self, *args, **kwargs):
            pass

        def divider(self, *args, **kwargs):
            pass

        def file_uploader(self, *args, **kwargs):
            return []

        def slider(self, *args, **kwargs):
            return 8

        def button(self, *args, **kwargs):
            return False

        def checkbox(self, *args, **kwargs):
            return kwargs.get("value", False)

        def warning(self, *args, **kwargs):
            pass

        def info(self, *args, **kwargs):
            pass

        def success(self, *args, **kwargs):
            pass

        def error(self, *args, **kwargs):
            pass

        @property
        def sidebar(self):
            return self

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    st = DummySt()
import os
import io
import logging
import pandas as pd
import matplotlib.pyplot as plt
import tempfile
import re
from pdf_redactor import redact_text
from dotenv import load_dotenv
from utils.output_detection import detect_output_type
from guards.rag_policy import (
    RAG_SYSTEM_PROMPT,
    SAFE_REFUSAL,
    sanitize_retrieved_content,
    validate_generated_answer,
    validate_user_question,
)

# Import privacy-aware output formatter
try:
    from utils.privacy_output_formatter import (
        generate_table,
        generate_excel,
        generate_chart,
        generate_docx,
        generate_pdf,
        generate_pptx,
        PrivacyAwareOutputFormatter,
    )
except ImportError:
    from utils.artifact_generator import (
        generate_table,
        generate_excel,
        generate_chart,
        generate_docx,
        generate_pdf,
        generate_pptx,
    )

    PrivacyAwareOutputFormatter = None

# Import enhanced privacy guards
try:
    from guard_utils import check_prompt, check_response, PrivacySanitizer
    from privacy_config import get_privacy_config, is_strict_mode
except ImportError:

    def check_prompt(prompt: str):
        return True, prompt

    def check_response(response: str, prompt: str = ""):
        return True, response

    PrivacySanitizer = None
    get_privacy_config = None
    is_strict_mode = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

try:
    from deepeval.metrics import (
        AnswerRelevancyMetric,
        FaithfulnessMetric,
    )
    from deepeval.test_case import LLMTestCase
except ModuleNotFoundError:
    AnswerRelevancyMetric = FaithfulnessMetric = LLMTestCase = None

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama3-70b-8192",
    "mixtral-8b-32768",
]

# ============================================================================
# PRIVACY CONFIGURATION
# ============================================================================

PRIVACY_LEVEL = os.getenv("PRIVACY_LEVEL", "STANDARD").upper()
logger.info(f"Privacy Level: {PRIVACY_LEVEL}")

# ============================================================================
# STREAMLIT SETUP
# ============================================================================


st.markdown(
    """
<style>
  /* Hide Streamlit default header/footer */
  #MainMenu, footer, header {visibility: hidden;}

  /* Full page dark background */
  .stApp { background-color: #212121; }

  /* Sidebar */
  section[data-testid=\"stSidebar\"] {
      background-color: #2f2f2f !important;
  }
  section[data-testid=\"stSidebar\"] * { color: #ececec !important; }

  /* Chat container */
  .chat-wrap { max-width: 800px; margin: 0 auto; padding-bottom: 20px; }

  /* User bubble */
  .user-bubble {
      background: #2f2f2f;
      color: #ececec;
      border-radius: 18px 18px 4px 18px;
      padding: 12px 18px;
      margin: 8px 0 8px 80px;
      font-size: .95rem;
      line-height: 1.6;
      word-break: break-word;
  }

  /* Assistant bubble */
  .bot-bubble {
      background: #1a1a2e;
      color: #e8e8f0 !important;
      border-left: 3px solid #6c63ff;
      border-radius: 0 18px 18px 18px;
      padding: 14px 18px;
      margin: 8px 80px 8px 0;
      font-size: .95rem;
      line-height: 1.8;
      word-break: break-word;
  }

  /* Source chips */
  .src-chip {
      display: inline-block;
      background: #2a2a4a;
      color: #a5b4fc !important;
      border: 1px solid #4f46e5;
      border-radius: 20px;
      padding: 2px 10px;
      font-size: .75rem;
      margin: 3px 3px 0 0;
  }

  /* Title */
  .app-title {
      font-size: 1.6rem;
      font-weight: 800;
      color: #a5b4fc;
      margin-bottom: 4px;
  }
  .app-sub {
      font-size: .85rem;
      color: #6b7280;
      margin-bottom: 20px;
  }

  /* Status pill */
  .pill-green {
      background:#065f46; color:#6ee7b7 !important;
      border-radius:20px; padding:3px 12px;
      font-size:.78rem; font-weight:700;
  }
  .pill-gray {
      background:#374151; color:#9ca3af !important;
      border-radius:20px; padding:3px 12px;
      font-size:.78rem; font-weight:700;
  }

  /* Input box override */
  .stChatInput textarea {
      background:#2f2f2f !important;
      color:#ececec !important;
      border:1px solid #4b5563 !important;
      border-radius:12px !important;
  }

  /* Buttons */
  .stButton>button {
      border-radius:10px !important;
      font-weight:700 !important;
      background:#4f46e5 !important;
      color:white !important;
      border:none !important;
  }
  .stButton>button:hover { background:#4338ca !important; }

  div[data-testid=\"stExpander\"] {
      background:#1e1e2e;
      border:1px solid #374151;
      border-radius:8px;
  }
</style>
""",
    unsafe_allow_html=True,
)

for k, v in [
    ("vectorstore", None),
    ("bm25", None),
    ("all_docs", []),
    ("chat_history", []),
    ("pdf_names", []),
    ("deepeval_enabled", True),
]:
    if k not in st.session_state:
        st.session_state[k] = v


@st.cache_resource(show_spinner="Loading embedding model…")
def get_embeddings():
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError:
        from langchain_community.embeddings import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def make_splitter():
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except ImportError:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
    return RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=80,
        separators=["\n\n", "\n", ". ", "? ", "! ", ", ", " ", ""],
    )


def process_pdfs(files):
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_community.vectorstores import FAISS
    from rank_bm25 import BM25Okapi

    splitter = make_splitter()
    all_docs, names = [], []

    with tempfile.TemporaryDirectory() as tmp:
        for uf in files:
            path = os.path.join(tmp, uf.name)
            with open(path, "wb") as f:
                f.write(uf.read())
            try:
                pages = PyPDFLoader(path).load()
                if not pages:
                    st.warning(f"No text in `{uf.name}` — scanned PDF?")
                    continue
                # Redact PII from each page's content before further processing
                for p in pages:
                    p.page_content = redact_text(p.page_content)
                    p.metadata["source_file"] = uf.name
                chunks = splitter.split_documents(pages)
                all_docs.extend(chunks)
                names.append(uf.name)
                st.caption(f"{uf.name} → {len(chunks)} chunks")
            except Exception as e:
                st.warning(f"Error reading {uf.name}: {e}")

    if not all_docs:
        return None, None, [], []

    vs = FAISS.from_documents(all_docs, get_embeddings())
    tokenized = [doc.page_content.lower().split() for doc in all_docs]
    bm25 = BM25Okapi(tokenized)
    return vs, bm25, all_docs, names


def hybrid_retrieve(question, vectorstore, bm25, all_docs, top_k=8):
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


def build_messages(question, context, chat_history):
    messages = [{"role": "system", "content": RAG_SYSTEM_PROMPT}]
    for entry in chat_history[-4:]:
        messages.append({"role": entry["role"], "content": entry["content"]})
    user_msg = f"DOCUMENT CONTEXT:\n{context}\n\nQUESTION: {question}\n\nAnswer based strictly on the context above:"
    messages.append({"role": "user", "content": user_msg})
    return messages


def evaluate_response(question: str, answer: str, context: str) -> dict:
    """Evaluate an answer against the exact retrieved PDF context for this query.

    Deepeval is used when a judge model is configured. Otherwise, this returns a
    deterministic fallback so dynamic Streamlit PDF uploads never break.
    """

    def _tokens(text: str) -> set:
        stopwords = {
            "a",
            "an",
            "and",
            "are",
            "as",
            "at",
            "based",
            "be",
            "by",
            "does",
            "for",
            "from",
            "in",
            "is",
            "it",
            "of",
            "on",
            "or",
            "pdf",
            "say",
            "says",
            "the",
            "to",
            "what",
            "with",
        }
        return {
            w.strip(".,!?()[]:;\"'").lower()
            for w in text.split()
            if w.strip(".,!?()[]:;\"'").lower()
            and w.strip(".,!?()[]:;\"'").lower() not in stopwords
        }

    def _fallback(error: str = "") -> dict:
        q_words = _tokens(question)
        a_words = _tokens(answer)
        c_words = _tokens(context)
        answer_context_overlap = len(a_words & c_words) / max(len(a_words), 1)
        question_answer_overlap = len(q_words & a_words) / max(len(q_words), 1)
        claims_pdf_context = bool(
            re.search(r"\b(pdf|document|context)\b.{0,30}\b(says|mentions|states|contains)\b", answer, re.IGNORECASE)
            or re.search(r"\b(says|mentions|states|contains)\b.{0,30}\b(pdf|document|context)\b", answer, re.IGNORECASE)
        )

        relevancy_score = 1 if question_answer_overlap >= 0.25 else 0
        if not context and claims_pdf_context:
            relevancy_score = 0
        if context:
            faithfulness_score = 1 if answer_context_overlap >= 0.35 else 0
        else:
            faithfulness_score = 0 if claims_pdf_context else relevancy_score
        hallucination_score = faithfulness_score
        overall = round((relevancy_score + faithfulness_score) / 2, 2)

        return {
            "mode": "fallback",
            "error": error,
            "relevancy": relevancy_score,
            "hallucination": hallucination_score,
            "faithfulness": faithfulness_score,
            "contextual_recall": faithfulness_score,
            "overall_score": overall,
            "passed": bool(relevancy_score and faithfulness_score),
            "metrics": {
                "answer_relevancy": {
                    "score": float(relevancy_score),
                    "success": bool(relevancy_score),
                    "reason": "Keyword overlap between question and answer.",
                },
                "faithfulness": {
                    "score": float(faithfulness_score),
                    "success": bool(faithfulness_score),
                    "reason": "Keyword overlap between answer and retrieved PDF context.",
                },
            },
        }

    judge_model = os.getenv("DEEPEVAL_MODEL", "").strip() or None
    can_use_deepeval = (
        AnswerRelevancyMetric is not None
        and FaithfulnessMetric is not None
        and LLMTestCase is not None
        and (judge_model or os.getenv("OPENAI_API_KEY"))
    )

    if not can_use_deepeval:
        return _fallback("Deepeval judge model is not configured.")

    try:
        test_case = LLMTestCase(
            input=question,
            actual_output=answer,
            retrieval_context=[context] if context else [],
            context=[context] if context else [],
        )
        metric_specs = [
            ("answer_relevancy", AnswerRelevancyMetric),
            ("faithfulness", FaithfulnessMetric),
        ]
        metric_results = {}
        scores = []

        for name, metric_cls in metric_specs:
            metric = metric_cls(
                threshold=float(os.getenv("DEEPEVAL_THRESHOLD", "0.5")),
                model=judge_model,
                include_reason=True,
                async_mode=False,
            )
            score = metric.measure(test_case, _show_indicator=False)
            score = float(score if score is not None else metric.score)
            scores.append(score)
            metric_results[name] = {
                "score": round(score, 3),
                "success": bool(metric.success),
                "reason": getattr(metric, "reason", ""),
            }

        relevancy_score = 1 if metric_results["answer_relevancy"]["success"] else 0
        faithfulness_score = 1 if metric_results["faithfulness"]["success"] else 0
        overall = round(sum(scores) / max(len(scores), 1), 3)

        return {
            "mode": "deepeval",
            "error": "",
            "relevancy": relevancy_score,
            "hallucination": faithfulness_score,
            "faithfulness": faithfulness_score,
            "contextual_recall": faithfulness_score,
            "overall_score": overall,
            "passed": all(item["success"] for item in metric_results.values()),
            "metrics": metric_results,
        }
    except Exception as e:
        logger.warning(f"Deepeval evaluation failed, using fallback: {e}")
        return _fallback(str(e))


def render_eval_summary(evaluation: dict):
    if not evaluation:
        return

    mode = evaluation.get("mode", "fallback")
    status = "passed" if evaluation.get("passed") else "needs review"
    score = evaluation.get("overall_score")
    st.caption(f"Evaluation: {status} | score {score} | {mode}")


def get_answer(question, vectorstore, bm25, all_docs, chat_history, top_k=8):
    from groq import Groq

    question_guard = validate_user_question(question)
    if not question_guard.passed:
        return question_guard.sanitized_text or SAFE_REFUSAL, [], ""

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
    messages = build_messages(question, context, chat_history)
    client = Groq(api_key=GROQ_API_KEY)
    last_error = None
    for model in GROQ_MODELS:
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0,
                max_tokens=2048,
            )
            answer_text = resp.choices[0].message.content.strip()
            answer_guard = validate_generated_answer(answer_text)
            if not answer_guard.passed:
                return answer_guard.sanitized_text or SAFE_REFUSAL, sources, context
            return answer_text, sources, context
        except Exception as e:
            last_error = str(e)
            if any(
                x in last_error
                for x in ["decommissioned", "model_not_found", "404", "not found"]
            ):
                continue
            raise Exception(last_error)
    raise Exception(f"All models failed. Last: {last_error}")


with st.sidebar:

    st.subheader("Upload PDFs")
    uploaded = st.file_uploader(
        "Choose PDF files", type=["pdf"], accept_multiple_files=True
    )
    top_k = st.slider(
        "Retrieval depth", 5, 15, 8, help="Higher = more context per question"
    )
    st.session_state.deepeval_enabled = st.checkbox(
        "Evaluate answers",
        value=st.session_state.deepeval_enabled,
        help="Runs Deepeval when configured, otherwise uses a local fallback check.",
    )
    if st.button(" Process PDFs ke liye use kre", use_container_width=True):
        if not uploaded:
            st.warning("re baba ek pdf toh dal.")
        else:
            with st.spinner("Building Hybrid RAG index…"):
                vs, bm25, docs, names = process_pdfs(uploaded)
            if vs:
                st.session_state.vectorstore = vs
                st.session_state.bm25 = bm25
                st.session_state.all_docs = docs
                st.session_state.pdf_names = names
                st.session_state.chat_history = []
                st.success(f"{len(names)} PDFs indexed with PII protection!")
            else:
                st.error("No text extracted.")
    st.divider()
    st.subheader("Indexed Files")
    if st.session_state.pdf_names:
        for n in st.session_state.pdf_names:
            st.markdown(f"- `{n}`")
        if st.button("Clear Chat & Docs", use_container_width=True):
            for k in ["vectorstore", "bm25", "all_docs", "chat_history", "pdf_names"]:
                st.session_state[k] = None if k in ["vectorstore", "bm25"] else []
            st.rerun()
    else:
        st.info("No PDFs yet.")


st.markdown('<p class="app-title">PDF Chat</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="app-sub">Sawal kroge? PDF ke baare me </p>',
    unsafe_allow_html=True,
)

if st.session_state.vectorstore is None:
    st.markdown(
        """
    <div style="text-align:center; padding:60px 20px; color:#6b7280;">
        <div style="font-size:4rem;"></div>
        <h3 style="color:#9ca3af;">Pdf dal ley bhai</h3>
        <p>Use the sidebar to upload and process your PDF files</p>
    </div>
    """,
        unsafe_allow_html=True,
    )
else:
    for entry in st.session_state.chat_history:
        if entry["role"] == "user":
            st.markdown(
                f'<div class="user-bubble">{entry["content"]}</div>',
                unsafe_allow_html=True,
            )
        else:
            ans = entry["content"]
            ans = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", ans)
            ans = ans.replace("\n", "<br>")
            st.markdown(f'<div class="bot-bubble">{ans}</div>', unsafe_allow_html=True)
            if entry.get("sources"):
                seen = set()
                chips = ""
                for s in entry["sources"]:
                    key = f"{s['file']}|{s['page']}"
                    if key not in seen:
                        seen.add(key)
                        chips += (
                            f'<span class="src-chip">{s["file"]} p.{s["page"]}</span>'
                        )
                if chips:
                    st.markdown(
                        f'<div style="margin:4px 0 12px 0">{chips}</div>',
                        unsafe_allow_html=True,
                    )
            if entry.get("evaluation"):
                render_eval_summary(entry["evaluation"])
    question = st.chat_input("Sawal Jawab pesh krta hai kon krega ROADPATI…")
    if question:
        st.markdown(
            f'<div class="user-bubble">{question}</div>', unsafe_allow_html=True
        )
        st.session_state.chat_history.append(
            {"role": "user", "content": question, "sources": []}
        )

        # ====================================================================
        # PRIVACY: INPUT CHECK
        # ====================================================================
        prompt_safe, sanitized_prompt = check_prompt(question)
        if not prompt_safe:
            st.error(f"**Prompt Security Block:** {sanitized_prompt}")
            st.info(
                "Your input was blocked for security/privacy reasons. Please rephrase your question."
            )
            logger.warning(f"Prompt blocked: {sanitized_prompt}")
        else:
            try:
                # Use sanitized prompt if available
                query_to_use = sanitized_prompt if sanitized_prompt else question

                # Get answer from RAG system
                with st.spinner(" Retrieving and processing…"):
                    answer, sources, context = get_answer(
                        query_to_use,
                        st.session_state.vectorstore,
                        st.session_state.bm25,
                        st.session_state.all_docs,
                        st.session_state.chat_history,
                        top_k=top_k,
                    )

                # ================================================================
                # PRIVACY: OUTPUT CHECK
                # ================================================================
                response_safe, sanitized_answer = check_response(answer, query_to_use)

                if not response_safe:
                    st.warning(
                        f" **Output Security Block:** Content filtered for privacy/safety"
                    )
                    sanitized_answer = "I cannot provide that response due to security/privacy policies."
                    logger.warning(f"Response blocked: {response_safe}")
                    answer = sanitized_answer
                else:
                    answer = sanitized_answer if sanitized_answer else answer

                evaluation = None
                if st.session_state.deepeval_enabled:
                    with st.spinner("Evaluating answer…"):
                        evaluation = evaluate_response(query_to_use, answer, context)

                # Display the answer
                ans_html = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", answer)
                ans_html = ans_html.replace("\n", "<br>")

                output_type = detect_output_type(query_to_use)

                if output_type == "text":
                    st.markdown(
                        f'<div class="bot-bubble">{ans_html}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    # Handle structured output types (table, chart, etc.)
                    file_bytes = None
                    filename = ""
                    mime = ""

                    if output_type == "table":
                        df = generate_table(answer)
                        st.subheader(" Result Table")
                        st.dataframe(df, use_container_width=True)
                        file_bytes = generate_excel(df)
                        filename = "answer.xlsx"
                        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                    elif output_type == "chart":
                        q_lower = query_to_use.lower()
                        if "pie" in q_lower:
                            chart_type = "pie"
                        elif "histogram" in q_lower:
                            chart_type = "histogram"
                        elif "bar" in q_lower:
                            chart_type = "bar"
                        else:
                            chart_type = "line"

                        file_bytes = generate_chart(answer, chart_type)
                        st.subheader(f"{chart_type.title()} Chart")
                        st.image(file_bytes)
                        filename = f"{chart_type}_chart.png"
                        mime = "image/png"

                    elif output_type == "excel":
                        df = generate_table(answer)
                        file_bytes = generate_excel(df)
                        st.subheader("Excel Export")
                        st.dataframe(df, use_container_width=True)
                        filename = "answer.xlsx"
                        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                    elif output_type == "docx":
                        file_bytes = generate_docx(answer)
                        filename = "report.docx"
                        mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        st.subheader(" Word Document")

                    elif output_type == "pdf":
                        file_bytes = generate_pdf(answer)
                        filename = "report.pdf"
                        mime = "application/pdf"
                        st.subheader(" PDF Document")

                    elif output_type == "pptx":
                        file_bytes = generate_pptx(answer)
                        filename = "presentation.pptx"
                        mime = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
                        st.subheader("🎬 PowerPoint Presentation")

                    # Download button
                    if file_bytes:
                        st.download_button(
                            label=f"⬇Download {output_type.upper()}",
                            data=file_bytes,
                            file_name=filename,
                            mime=mime,
                            use_container_width=True,
                        )

                    # Also show text representation
                    st.markdown(
                        f'<div class="bot-bubble">{ans_html}</div>',
                        unsafe_allow_html=True,
                    )

                # Display sources
                if sources:
                    st.markdown("**Reference lelo Reference: **")
                    seen, chips = set(), ""
                    for s in sources:
                        key = f"{s['file']}|{s['page']}"
                        if key not in seen:
                            seen.add(key)
                            chips += f'<span class="src-chip">{s["file"]} • p.{s["page"]}</span>'
                    st.markdown(
                        f'<div style="margin:4px 0 12px 0">{chips}</div>',
                        unsafe_allow_html=True,
                    )

                if evaluation:
                    render_eval_summary(evaluation)

                # Add response to chat history
                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                        "evaluation": evaluation,
                    }
                )

            except Exception as e:
                logger.error(f"Error processing question: {e}")
                st.error(f" **Error:** {str(e)}")
                st.info("Please try rephrasing your question or upload different PDFs.")
