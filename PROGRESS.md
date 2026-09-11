# AegisFlow — Build Progress

Tracking against the senior-engineer phased roadmap (6 phases, ~30 days effort).

## Status: Phase 1 — Foundations & Data Layer (in progress)

### ✅ Completed

**Design**
- [x] ADR-001: Laravel + Python split architecture — `docs/adr/001-laravel-python-split.md`
- [x] ADR-002: Risky-PR proxy label definition — `docs/adr/002-risky-pr-label-definition.md`

**Build**
- [x] Repo scaffolded: `AegisBackend/` (Laravel 13) + `ml-service/` (Python/FastAPI)
- [x] Git initialized, pushed to GitHub, clean working tree
- [x] Laravel boots successfully (`php artisan serve` verified)
- [x] Python venv + all core dependencies installed and importable
- [x] GitHub API data collector built (`app/collectors/github_collector.py`):
  - [x] Pagination
  - [x] Rate-limit detection + backoff
  - [x] Disk caching layer
  - [x] Verified live against real GitHub API (authenticated, 5000/hr limit confirmed)
  - [x] Cache hit/miss behavior confirmed (1.59s cold call → 0.01s cached call)

### 🚧 Not yet started

**Phase 1 remaining**
- [ ] Postgres schema design (ERD) for repos / pull_requests / files_changed / labels / predictions
- [ ] Laravel migrations implementing the schema
- [ ] Data cleaning pipeline
- [ ] Label generation implementing ADR-002's rules
- [ ] Labeled dataset stored in Postgres
- [ ] Label-quality sanity check (10 manually reviewed PRs)

**Phase 2 — ML Core**
- [ ] ADR-003: feature set + leakage rationale
- [ ] Evaluation protocol doc
- [ ] Feature engineering module
- [ ] Logistic Regression baseline → Random Forest → XGBoost comparison
- [ ] Versioned model registry

**Phase 3 — Backend Services & Contracts**
- [ ] OpenAPI spec for ml-service
- [ ] Webhook sequence diagram
- [ ] FastAPI `/predict` + `/health` endpoints
- [ ] Laravel webhook receiver + signature verification + queue
- [ ] Redis caching + invalidation policy
- [ ] LLM summarization (versioned prompt templates)

**Phase 4 — Frontend**
- [ ] Dashboard, PR list/detail, risk visualization
- [ ] GitHub OAuth
- [ ] Loading/error/empty states

**Phase 5 — DevOps & Infra**
- [ ] ADR-004: deployment topology
- [ ] Docker Compose (local parity)
- [ ] CI: test → lint → security scan → build
- [ ] CD: staging auto-deploy, production on tag
- [ ] CloudWatch alerting

**Phase 6 — Hardening & Launch**
- [ ] Architecture diagram + final README
- [ ] Post-mortem writeup
- [ ] Demo rehearsal
- [ ] Launch post

---
_Last updated: manually — update this file at the end of each work session._
