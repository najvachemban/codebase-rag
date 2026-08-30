"""
Phase 2, Step 3: AST-aware chunking.

Responsibility: parse a source file with Tree-sitter and extract each
top-level function as a complete, structurally-correct CodeChunk --
never splitting a function's signature from its body.
"""

from dataclasses import dataclass

from tree_sitter_languages import get_parser


@dataclass
class CodeChunk:
    """A single function-level chunk of code, with metadata."""
    function_name: str
    source_code: str
    start_line: int
    end_line: int
    language: str


def extract_function_chunks(source_code: str, language: str = "python") -> list[CodeChunk]:
    """
    Parse source code and extract each top-level function as a CodeChunk.

    Args:
        source_code: the full text content of a source file.
        language: language name understood by tree_sitter_languages (e.g. "python").

    Returns:
        List of CodeChunk objects, one per top-level function found.
    """
    parser = get_parser(language)
    source_bytes = source_code.encode("utf-8")
    tree = parser.parse(source_bytes)
    root = tree.root_node

    chunks: list[CodeChunk] = []

    for node in root.children:
        if node.type != "function_definition":
            continue

        # The function name lives in a child node of type "identifier",
        # not as a direct property of the function_definition node itself.
        name_node = next(
            (child for child in node.children if child.type == "identifier"),
            None,
        )
        function_name = (
            source_bytes[name_node.start_byte:name_node.end_byte].decode("utf-8")
            if name_node is not None
            else "<unknown>"
        )

        function_source = source_bytes[node.start_byte:node.end_byte].decode("utf-8")

        chunks.append(
            CodeChunk(
                function_name=function_name,
                source_code=function_source,
                start_line=node.start_point[0] + 1,  # tree-sitter is 0-indexed
                end_line=node.end_point[0] + 1,
                language=language,
            )
        )

    return chunks