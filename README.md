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

- [ ] **Phase 9 — Repository-Aware Retrieval**
  - [ ] Metadata filtering (language, path, class, function)

- [ ] **Phase 10 — Graph/Dependency-Aware RAG**
  - [ ] Demonstrate a concrete retrieval failure first
  - [ ] Lightweight call-graph construction

- [ ] **Phase 11 — Context Construction**
  - [ ] Chunk ordering, dedup, token budget management

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

- [ ] **Phase 20 — Interview Preparation**
  - [ ] Review architecture, trade-offs, and metrics for interview readiness
