## Roadmap / Phase-wise Tasks

- [x] **Phase 0 — System Design**
  - [x] RAG vs Codebase RAG concepts
  - [x] Architecture decision: MySQL + Chroma (polyglot persistence)
  - [x] Project skeleton scaffolded

- [x] **Phase 1 — Repository Ingestion**
  - [x] Clone GitHub repo (shallow clone, isolated temp dir)
  - [x] Walk file tree with directory/extension filtering
  - [x] Respect repository `.gitignore` rules
  - [x] Detect and reject binary files
  - [x] Extract file metadata (path, language, size)
  - [x] Design MySQL schema (repositories, files)
  - [x] Persist ingestion results to MySQL

- [x] **Phase 2 — Code Parsing**
  - [x] Compare fixed-size vs function-level vs AST-aware chunking
  - [x] Integrate Tree-sitter (or chosen parser)
  - [x] Extract function/class-level chunks with metadata

- [x] **Phase 3 — Embeddings**
  - [x] Choose embedding model
  - [x] Build embedding pipeline

- [x] **Phase 4 — Vector Database**
  - [x] Chroma schema/collection design
  - [x] Link MySQL chunk IDs to Chroma vectors

- [x] **Phase 5 — Basic Retrieval**
  - [x] End-to-end vector-search RAG pipeline
  - [x] Citations (file, function, lines)
  - [x] Verified with real Gemini generation against a real repo (requests)
  - [!] Known gap: duplicate citations when multiple windows of the same chunk are retrieved
  
- [x] **Phase 6 — Hybrid Retrieval**
  - [x] BM25 keyword search index
  - [x] Reciprocal Rank Fusion (RRF)
  - [x] Compared vector-only vs BM25-only vs hybrid on real queries
  
- [x] **Phase 7 — Reranking**
  - [x] Cross-encoder reranking stage (ms-marco-MiniLM-L-6-v2)
  - [x] Verified reranking correctly demotes test code vs implementation code

- [x] **Phase 8 — Query Understanding**
  - [x] LLM-based query rewriting implemented
  - [x] Tested against real repo — no clear improvement observed;
        root cause traced to question/corpus mismatch, not rewriting quality.
        Kept as opt-in, not default-on, pending further testing with
        better-matched questions.

- [x] **Phase 9 — Repository-Aware Retrieval**
  - [x] Metadata filtering (language, file path prefix, class, repo)
  - [x] Applied before fusion, not just at display time
  - [x] Noted: filter value depends on corpus heterogeneity, not universal
  
- [x] **Phase 10 — Graph/Dependency-Aware RAG**
  - [x] Demonstrated concrete failure first (top-K missing a real callee)
  - [x] AST-based call extraction (Tree-sitter)
  - [x] Same-file-scoped dependency expansion, fixing the demonstrated gap
  - [!] Known limitation: cross-file calls (imports) are not resolved

- [x] **Phase 10.5 — Exact-Name Retrieval Shortcut** *(refinement, added after real-world testing)*
  - [x] Diagnosed a real failure: short, generic-sounding orchestrator functions
        (e.g. `Session.request()`) were invisible to BOTH vector search and BM25,
        due to weak/shared vocabulary
  - [x] Built exact-name matching to guarantee named functions/classes are
        included in the candidate pool
  - [x] Found and fixed a follow-up bug: exact matches were being added to the
        pool but then discarded by reranking, which overwrote their priority.
        Fixed by pinning exact matches to survive reranking.

- [x] **Phase 11 — Context Construction**
  - [x] Token-budgeted, priority-ordered context assembly
  - [x] Direct results prioritized over dependency-expanded results
  - [x] Results dropped whole (never truncated mid-function) when over budget

- [x] **Phases 5–11 — Consolidated**
  - [x] Full pipeline wired: hybrid retrieval → exact-name shortcut → rerank
        (with pinning) → dependency expansion → context budget → generation
  - [x] `RetrievalContext` bundles expensive setup (BM25, function index,
        name index) for reuse across queries

- [ ] **Phase 12 — LLM Generation**
  - [ ] Prompt design for grounded, citation-backed answers

- [ ] **Phase 13 — Hallucination Handling**
  - [ ] Evidence sufficiency check + abstention

- [ ] **Phase 14 — RAG Evaluation**
  - [ ] Build eval dataset
  - [ ] Retrieval metrics (Recall@K, Precision@K, MRR)
  - [ ] Generation metrics (faithfulness, relevance)

- [ ] **Phase 15 — Backend**
  - [ ] Production FastAPI endpoints
  - [ ] Background indexing jobs

- [ ] **Phase 16 — Frontend**
  - [ ] React chat UI with citations

- [ ] **Phase 17 — Production Improvements**
  - [ ] Caching, rate limiting, logging, security

- [ ] **Phase 18 — Docker**
  - [ ] Full docker-compose (backend, frontend, MySQL, Chroma)

- [ ] **Phase 19 — Deployment**
  - [ ] Public URL deployment

## Tech Stack 
- Reranking: cross-encoder (ms-marco-MiniLM-L-6-v2)
- Keyword search: BM25 (rank_bm25)


## Known Issues & Lessons Learned

- **Duplicate citations**: long functions split into multiple embedding
  windows can appear as separate "hits" if more than one window scores
  highly — not yet deduplicated at the final citation level.
- **Cross-file dependency resolution**: the call graph only resolves
  callees within the SAME FILE as the caller; imported functions from
  other files aren't linked.
- **Short orchestrator functions**: functions that mostly just call other
  functions (thin coordinators) can be invisible to both dense and sparse
  retrieval, since their own text has little distinctive content. Fixed
  via an exact-name-match shortcut for cases where the user names the
  function directly; still a gap for vaguer phrasing of the same question.
- **Query rewriting**: implemented but not proven beneficial in initial
  testing; kept as opt-in pending further evaluation (Phase 14).