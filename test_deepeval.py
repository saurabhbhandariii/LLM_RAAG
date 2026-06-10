from deepeval.metrics import AnswerRelevancyMetric, HallucinationMetric
from app import evaluate_response

def test_deepeval_basic():
    q = "What is the purpose of LangChain?"
    a = "LangChain is a framework for building LLM‑powered applications."
    scores = evaluate_response(q, a, "")
    assert scores["relevancy"] == 1, "Relevancy should be true for a correct answer"
    assert scores["hallucination"] == 1, "Hallucination should be false for a correct answer"

def test_deepeval_hallucination():
    q = "What does the PDF say about the weather?"
    a = "The PDF mentions that the weather in Paris was sunny on 2023‑04‑01."
    scores = evaluate_response(q, a, "")
    assert scores["relevancy"] == 0, "Relevancy should be false for unrelated answer"
    assert scores["hallucination"] == 0, "Hallucination should be detected"
