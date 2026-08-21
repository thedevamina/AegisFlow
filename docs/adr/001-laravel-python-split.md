# ADR-001: Split architecture — Laravel core + Python ML service

## Status
Accepted

## Context
AegisFlow needs both a full web application (auth, dashboard, webhook handling,
queues) and an ML/data pipeline (feature engineering, model training, LLM
summarization). These are different domains with different tooling strengths:
Laravel is mature for web-app concerns (auth, queues, ORM, routing); Python
has the dominant ecosystem for ML (scikit-learn, XGBoost, pandas).

## Decision
Two services, one shared Postgres database:
- `AegisBackend/` (Laravel) owns auth, dashboard, webhook ingestion, DB schema
  (all migrations live here).
- `ml-service/` (FastAPI) owns data collection, feature engineering, model
  training/serving, and LLM summarization.
They communicate over HTTP for predictions (Laravel calls ml-service's
`/predict` endpoint) and share the same Postgres instance for reads.

## Consequences
**Positive:**
- Each service uses the best tool for its domain instead of forcing ML work
  into PHP or web-app plumbing into Python.
- Independently deployable/scalable — the ML service can be scaled separately
  from the web app if prediction load grows.

**Negative:**
- Two languages/runtimes to deploy, monitor, and keep in sync — more moving
  parts than a single-service app for a solo 4-week build.
- Schema changes need coordination: Laravel owns migrations, but ml-service
  reads/writes the same tables, so a migration can silently break the
  Python side if not communicated.
- Extra network hop (Laravel -> ml-service) on every prediction request.

## Alternatives considered
- **Pure Python (FastAPI) end-to-end**: simpler, one language, fewer moving
  parts. Rejected because the project's goal includes demonstrating the
  industry-common pattern of integrating ML into an existing web-framework
  architecture, and because splitting concerns is valuable for the
  portfolio/interview narrative even at added operational cost.
- **Pure Laravel with a PHP ML library**: rejected — PHP's ML/data-science
  ecosystem is far behind Python's; would mean building weaker models with
  worse tooling.
