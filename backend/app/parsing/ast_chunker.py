"""
Phase 2, Step 4: AST-aware chunking with class/method support,
docstrings, and import metadata.

Responsibility: parse a source file with Tree-sitter and extract every
function AND method as a complete, structurally-correct CodeChunk,
tagged with its class (if any), docstring, and the file's imports.
"""

from dataclasses import dataclass, field

from tree_sitter_languages import get_parser


@dataclass
class CodeChunk:
    """A single function- or method-level chunk of code, with metadata."""
    function_name: str
    class_name: str | None
    source_code: str
    docstring: str | None
    start_line: int
    end_line: int
    language: str
    imports: list[str] = field(default_factory=list)


def _get_identifier_text(node, source_bytes: bytes) -> str | None:
    """Find the 'identifier' child of a node and return its text."""
    name_node = next(
        (child for child in node.children if child.type == "identifier"),
        None,
    )
    if name_node is None:
        return None
    return source_bytes[name_node.start_byte:name_node.end_byte].decode("utf-8")


def _extract_docstring(function_node, source_bytes: bytes) -> str | None:
    """
    A Python docstring is the first statement in a function's body,
    IF that statement is a bare string expression.
    """
    body_node = next(
        (child for child in function_node.children if child.type == "block"),
        None,
    )
    if body_node is None or len(body_node.children) == 0:
        return None

    first_statement = body_node.children[0]
    if first_statement.type == "expression_statement":
        string_node = first_statement.children[0] if first_statement.children else None
        if string_node is not None and string_node.type == "string":
            raw = source_bytes[string_node.start_byte:string_node.end_byte].decode("utf-8")
            return raw.strip("\"' \n")

    return None


def _extract_imports(root, source_bytes: bytes) -> list[str]:
    """Collect all top-level import statements in the file, as raw text."""
    imports = []
    for node in root.children:
        if node.type in ("import_statement", "import_from_statement"):
            text = source_bytes[node.start_byte:node.end_byte].decode("utf-8")
            imports.append(text)
    return imports


def _walk_for_functions(node, source_bytes: bytes, language: str,
                         imports: list[str], class_name: str | None = None) -> list[CodeChunk]:
    """
    Recursively walk the tree. When a class_definition is found, recurse
    into its body with class_name set, so methods are correctly tagged.
    When a function_definition is found, extract it as a CodeChunk.
    """
    chunks: list[CodeChunk] = []

    for child in node.children:
        if child.type == "class_definition":
            found_class_name = _get_identifier_text(child, source_bytes) or "<unknown class>"
            body_node = next((c for c in child.children if c.type == "block"), None)
            if body_node is not None:
                chunks.extend(
                    _walk_for_functions(body_node, source_bytes, language, imports, found_class_name)
                )

        elif child.type == "function_definition":
            function_name = _get_identifier_text(child, source_bytes) or "<unknown function>"
            function_source = source_bytes[child.start_byte:child.end_byte].decode("utf-8")
            docstring = _extract_docstring(child, source_bytes)

            chunks.append(
                CodeChunk(
                    function_name=function_name,
                    class_name=class_name,
                    source_code=function_source,
                    docstring=docstring,
                    start_line=child.start_point[0] + 1,
                    end_line=child.end_point[0] + 1,
                    language=language,
                    imports=imports,
                )
            )
            # Note: we don't recurse into a function's own body here, so
            # nested/inner functions are intentionally out of scope for now.

    return chunks


def extract_function_chunks(source_code: str, language: str = "python") -> list[CodeChunk]:
    """
    Parse source code and extract every function and method as a CodeChunk,
    including class association, docstrings, and file-level imports.
    """
    parser = get_parser(language)
    source_bytes = source_code.encode("utf-8")
    tree = parser.parse(source_bytes)
    root = tree.root_node

    imports = _extract_imports(root, source_bytes)
    return _walk_for_functions(root, source_bytes, language, imports)