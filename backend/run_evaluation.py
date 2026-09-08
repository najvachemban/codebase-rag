"""
Phase 14: Compare retrieval configurations against the eval dataset.

Run this to get REAL numbers for: naive (vector-only) vs hybrid vs
hybrid+rerank vs full pipeline (+exact-match+dependencies) -- replacing
anecdotal "this seemed better" observations with measured comparisons.
"""

from app.storage.database import get_engine, get_session_factory
from app.storage.models import Chunk
from app.storage.vector_store import get_client, get_collection
from app.retrieval.rag_pipeline import build_retrieval_context, retrieve_candidates
from app.retrieval.basic_retrieval import retrieve as vector_only_retrieve
from app.evaluation.eval_dataset import EVAL_DATASET
from app.evaluation.metrics import recall_at_k, precision_at_k, mrr, hit_rate

engine = get_engine('sqlite:///./test.db')
Session = get_session_factory(engine)
session = Session()
all_chunks = session.query(Chunk).all()

client = get_client()
collection = get_collection(client)
ctx = build_retrieval_context(collection, all_chunks)


def to_qualified_name(result) -> str:
    if result.class_name:
        return f"{result.class_name}.{result.function_name}"
    return result.function_name


# Configs using the shared harness (hybrid_retrieve always fuses vector+BM25
# internally -- these toggle the LATER stages built on top of that fusion).
HYBRID_CONFIGS = {
    "Hybrid (no rerank/deps/exact)": dict(use_reranking=False, use_dependency_expansion=False, use_exact_match=False),
    "Hybrid + Rerank": dict(use_reranking=True, use_dependency_expansion=False, use_exact_match=False),
    "Full pipeline (+exact-match +deps)": dict(use_reranking=True, use_dependency_expansion=True, use_exact_match=True),
}


def evaluate(name: str, get_results_fn) -> None:
    recalls, precisions, mrrs, hits = [], [], [], []
    for eq in EVAL_DATASET:
        retrieved_names = get_results_fn(eq.question)
        recalls.append(recall_at_k(retrieved_names, eq.expected_functions))
        precisions.append(precision_at_k(retrieved_names, eq.expected_functions))
        mrrs.append(mrr(retrieved_names, eq.expected_functions))
        hits.append(hit_rate(retrieved_names, eq.expected_functions))

    avg = lambda lst: sum(lst) / len(lst) if lst else 0.0
    print(f"{name:<38} {avg(recalls):>9.3f} {avg(precisions):>12.3f} {avg(mrrs):>7.3f} {avg(hits):>8.3f}")


print(f"{'Configuration':<38} {'Recall@5':>9} {'Precision@5':>12} {'MRR':>7} {'HitRate':>8}")
print("-" * 78)

# TRUE vector-only baseline: uses basic_retrieval directly, bypassing
# BM25/RRF entirely -- this is the real "naive" starting point.
evaluate(
    "Vector-only (naive baseline)",
    lambda q: [to_qualified_name(r) for r in vector_only_retrieve(collection, q, top_k=5)],
)

for config_name, config_kwargs in HYBRID_CONFIGS.items():
    evaluate(
        config_name,
        lambda q, kw=config_kwargs: [to_qualified_name(r) for r in retrieve_candidates(ctx, q, top_k=5, **kw)],
    )