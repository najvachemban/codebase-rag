"""
Phase 10, Step 1: Lightweight call-graph extraction.

Responsibility: given a function's AST node, find the names of every
function it calls -- a minimal static analysis pass, NOT a full
cross-file resolver. This directly fixes the demonstrated failure:
retrieval finding an orchestrator function but missing its callees
when their wording doesn't match the query.
"""

from tree_sitter_languages import get_parser


def extract_called_functions(function_source: str) -> list[str]:
    """
    Parse a single function's source code and find the names of every
    function/method it calls, e.g. self.foo(...) -> "foo", bar(...) -> "bar".

    This is intentionally simple: it does not resolve WHICH class or
    module a call belongs to -- just the called name. Matching calls
    back to real chunks (by name, within the same file) happens in
    the retrieval expansion step, not here.
    """
    parser = get_parser("python")
    source_bytes = function_source.encode("utf-8")
    tree = parser.parse(source_bytes)

    called_names = set()

    def walk(node):
        if node.type == "call":
            # The first child of a 'call' node is what's being called --
            # could be a plain identifier (foo()) or an attribute access
            # (self.foo() -- an 'attribute' node whose last child is the name).
            func_node = node.children[0] if node.children else None
            if func_node is not None:
                if func_node.type == "identifier":
                    called_names.add(source_bytes[func_node.start_byte:func_node.end_byte].decode("utf-8"))
                elif func_node.type == "attribute":
                    # e.g. self.prepare_request -> take the last identifier child
                    attr_children = [c for c in func_node.children if c.type == "identifier"]
                    if attr_children:
                        last = attr_children[-1]
                        called_names.add(source_bytes[last.start_byte:last.end_byte].decode("utf-8"))

        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return sorted(called_names)