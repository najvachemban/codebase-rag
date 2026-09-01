"""
Phase 5, Step 2: Basic prompt construction from retrieved chunks.

This is a MINIMAL version -- real prompt engineering (grounding rules,
abstention behavior, citation formatting) is built properly in Phase 12.
For now, this just proves the end-to-end pipeline works.
"""

from app.retrieval.basic_retrieval import RetrievedChunk


def build_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    context_blocks = []
    for c in chunks:
        location = f"{c.file_path}:{c.start_line}-{c.end_line}"
        label = f"{c.class_name}.{c.function_name}" if c.class_name else c.function_name
        context_blocks.append(f"# {label} ({location})\n{c.text}")

    context = "\n\n".join(context_blocks)

    return f"""You are answering questions about a codebase using only the code provided below.

CODE CONTEXT:
{context}

QUESTION: {question}

Answer using only the code above. Reference specific file paths and function names in your answer.
If the provided code doesn't contain enough information to answer, say so clearly.
"""