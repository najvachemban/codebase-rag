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

- [ ] **Phase 2 — Code Parsing**
  - [ ] Compare fixed-size vs function-level vs AST-aware chunking
  - [ ] Integrate Tree-sitter (or chosen parser)
  - [ ] Extract function/class-level chunks with metadata

- [ ] **Phase 3 — Embeddings**
  - [ ] Choose embedding model
  - [ ] Build embedding pipeline

- [ ] **Phase 4 — Vector Database**
  - [ ] Chroma schema/collection design
  - [ ] Link MySQL chunk IDs to Chroma vectors

- [ ] **Phase 5 — Basic Retrieval**
  - [ ] End-to-end vector-search RAG pipeline
  - [ ] Citations (file, function, lines)

- [ ] **Phase 6 — Hybrid Retrieval**
  - [ ] BM25 keyword search
  - [ ] Result fusion (RRF or similar)

- [ ] **Phase 7 — Reranking**
  - [ ] Cross-encoder reranker
  - [ ] Measure improvement vs no reranking

- [ ] **Phase 8 — Query Understanding**
  - [ ] Query rewriting / expansion (only if measurably helpful)

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
