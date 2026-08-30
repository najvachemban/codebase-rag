from app.ingestion.github_ingestion import clone_repository, RepoCloneError

try:
    path = clone_repository("https://github.com/octocat/Hello-World")
    print("Cloned to:", path)
    print("Contents:", list(path.iterdir()))
except RepoCloneError as e:
    print("Clone failed:", e)