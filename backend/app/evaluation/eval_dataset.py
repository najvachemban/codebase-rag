"""
Phase 14: A small evaluation dataset with known-correct expected answers.

Each entry's expected_functions were verified through actual manual
investigation earlier in this project (e.g. the Session.request() case,
confirmed by reading the real requests source and tracing its call chain).

This starter set is intentionally small -- expand it as you verify more
questions against the real repo. A tiny, TRUSTED dataset is more useful
than a large, guessed one.
"""

from dataclasses import dataclass


@dataclass
class EvalQuestion:
    question: str
    expected_functions: set[str]  # qualified as "ClassName.function_name" or just "function_name"


EVAL_DATASET = [
    EvalQuestion(
        question="What happens when Session.request() is called — walk through the full flow?",
        expected_functions={
            "Session.request",
            "Session.prepare_request",
            "Session.merge_environment_settings",
            "Session.send",
        },
    ),
    # Add more entries here as you verify ground truth against your real repo.
    # Example pattern:
    # EvalQuestion(
    #     question="How is JWT validation performed?",
    #     expected_functions={"validate_token", "decode_jwt"},
    # ),
]