"""
Phase 15 Step 4: Full indexing pipeline, run as a background job.

Chains together Phases 1-4 exactly as they were built and tested
individually:
    clone_repository (Phase 1)
    -> walk_repository (Phase 1)
    -> gitignore filtering (Phase 1)
    -> binary-file filtering (Phase 1)
    -> extract_file_metadata (Phase 1)
    -> save_files (Phase 1)
    -> chunk_file (Phase 2)
    -> save_chunks (Phase 2)
    -> embed_chunks (Phase 3)
    -> add_embeddings (Phase 4)

Runs in its own DB session, separate from the request/response session,
because FastAPI BackgroundTasks execute AFTER the response has already
been sent -- by then, the endpoint's session (from Depends(get_db)) has
already been closed.

Known, deliberate limitation: re-running this on an already-indexed
repository does not delete prior File/Chunk rows or prior Chroma vectors
first. It will create duplicate rows, and old vectors become orphaned
(their chunk_id metadata won't match any current Chunk row). Safe
re-indexing (tear down old data first) is left for a later phase.
"""

import logging
import shutil

from app.ingestion.github_ingestion import clone_repository, RepoCloneError
from app.ingestion.file_walker import walk_repository
from app.ingestion.gitignore_filter import load_gitignore_spec, is_ignored
from app.ingestion.binary_detector import is_binary_file
from app.ingestion.file_metadata import extract_file_metadata
from app.parsing.chunk_pipeline import chunk_file
from app.embeddings.embedding_pipeline import embed_chunks
from app.storage.chunk_store import save_chunks
from app.storage.repository_store import save_files, update_repository_status
from app.storage.vector_store import get_client, get_collection, add_embeddings
from app.storage.database import get_engine, get_session_factory

logger = logging.getLogger(__name__)

_engine = get_engine()
_SessionFactory = get_session_factory(_engine)


def run_indexing_pipeline(repository_id: int, repo_url: str) -> None:
    """
    Run the full ingestion -> chunking -> embedding -> storage pipeline for
    one repository, updating its status in the database as it progresses.

    This function's own errors are caught and recorded via
    update_repository_status(..., status="failed", error_message=...)
    rather than raised -- since this runs in a background task, there is
    no HTTP request left to return an error response to. The database
    row IS the error-reporting mechanism here.
    """
    session = _SessionFactory()
    repo_path = None

    try:
        logger.info("Indexing started for repository_id=%s url=%s", repository_id, repo_url)

        # --- Phase 1: clone ---
        repo_path = clone_repository(repo_url)

        # --- Phase 1: walk + filter ---
        candidates = walk_repository(repo_path)
        gitignore_spec = load_gitignore_spec(repo_path)

        filtered_paths = [
            path
            for path in candidates
            if not is_ignored(path, repo_path, gitignore_spec)
            and not is_binary_file(path)
        ]

        file_metadata_list = [
            extract_file_metadata(path, repo_path) for path in filtered_paths
        ]

        logger.info(
            "repository_id=%s: %d candidate files, %d after gitignore/binary filtering",
            repository_id, len(candidates), len(file_metadata_list),
        )

        # --- Phase 1: persist File rows ---
        # save_files commits immediately, so file_rows have real ids. Order
        # is preserved (list comprehension in save_files), so zipping with
        # file_metadata_list below correctly pairs each metadata record with
        # its saved row.
        file_rows = save_files(session, repository_id, file_metadata_list)

        # --- Phase 2: chunk each file, persist Chunk rows ---
        all_chunk_rows = []
        for metadata, file_row in zip(file_metadata_list, file_rows):
            code_chunks = chunk_file(metadata)  # [] for unsupported languages or parse errors
            if not code_chunks:
                continue
            chunk_rows = save_chunks(session, file_row.id, code_chunks)
            all_chunk_rows.extend(chunk_rows)

        logger.info(
            "repository_id=%s: %d chunks extracted across %d files",
            repository_id, len(all_chunk_rows), len(file_rows),
        )

        # --- Phase 3 & 4: embed and store vectors, only if there's anything to embed ---
        if all_chunk_rows:
            embedded_windows = embed_chunks(all_chunk_rows)
            client = get_client()
            collection = get_collection(client)
            add_embeddings(collection, embedded_windows)
            logger.info(
                "repository_id=%s: %d embedded windows stored in Chroma",
                repository_id, len(embedded_windows),
            )
        else:
            logger.warning(
                "repository_id=%s: no chunks extracted (no supported-language "
                "files found) -- nothing to embed",
                repository_id,
            )

        update_repository_status(session, repository_id, "completed")
        logger.info("Indexing completed for repository_id=%s", repository_id)

    except RepoCloneError as e:
        logger.error("Clone failed for repository_id=%s: %s", repository_id, e)
        update_repository_status(session, repository_id, "failed", error_message=str(e))

    except Exception as e:
        # Deliberately broad: this is the last line of defense in a
        # background job with no caller left to catch anything. Any
        # unexpected failure (parsing, embedding, Chroma, DB) must still
        # land as a "failed" status rather than crash silently with the
        # repo stuck at "indexing" forever.
        logger.exception("Indexing failed unexpectedly for repository_id=%s", repository_id)
        update_repository_status(
            session, repository_id, "failed", error_message=f"Indexing failed: {e}"
        )

    finally:
        # The cloned repo directory is only needed during this job -- once
        # chunks/embeddings are persisted (or the job has failed), the temp
        # clone can be removed. clone_repository() itself never cleans up
        # after itself, so this is the only place that does.
        if repo_path is not None:
            shutil.rmtree(repo_path, ignore_errors=True)
        session.close()