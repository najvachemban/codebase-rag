"""
Phase 5, Step 2: The first full end-to-end RAG pipeline.

Question -> embed -> retrieve chunks -> build prompt -> LLM -> answer.
"""

from app.retrieval.basic_retrieval import retrieve
from app.generation.prompt_builder import build_prompt
from app.generation.llm_client import generate_answer


def answer_question(collection, question: str, top_k: int = 5) -> dict:
    """
    Run the full RAG pipeline for a single question.

    Returns a dict with the answer text AND the retrieved chunks used,
    so callers can display citations alongside the answer.
    """
    chunks = retrieve(collection, question, top_k=top_k)
    prompt = build_prompt(question, chunks)
    answer = generate_answer(prompt)

    return {
        "question": question,
        "answer": answer,
        "sources": [
            {
                "file_path": c.file_path,
                "function_name": c.function_name,
                "class_name": c.class_name,
                "lines": f"{c.start_line}-{c.end_line}",
            }
            for c in chunks
        ],
    }