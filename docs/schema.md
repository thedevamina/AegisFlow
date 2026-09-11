repos
├── id (PK)
├── full_name        (e.g. "psf/requests")
├── owner
├── name
├── collected_at
└── created_at, updated_at

pull_requests
├── id (PK)
├── repo_id (FK -> repos.id)
├── github_pr_number
├── title
├── author_login
├── author_pr_count       (author's PR history count at time of this PR — a feature)
├── state                 (open/closed/merged)
├── created_at_github
├── merged_at_github
├── closed_at_github
├── additions             (lines added)
├── deletions             (lines deleted)
├── changed_files_count
├── test_files_touched    (boolean — did the PR modify test files)
├── raw_payload           (JSONB — full original GitHub response, for reprocessing later)
└── created_at, updated_at

files_changed
├── id (PK)
├── pull_request_id (FK -> pull_requests.id)
├── filename
├── status            (added/modified/removed)
├── additions
├── deletions
└── created_at

labels
├── id (PK)
├── pull_request_id (FK -> pull_requests.id, unique)
├── is_risky          (boolean — the ADR-002 target label)
├── risk_reason       (enum/text: 'reverted' | 'hotfix_followup' | 'bug_linked' | null)
├── evaluated_at       (when the label was computed — labels can be recomputed later)
└── created_at, updated_at

predictions
├── id (PK)
├── pull_request_id (FK -> pull_requests.id)
├── model_version      (e.g. "xgboost_v1")
├── risk_score         (float 0-1)
├── risk_label         (predicted, not ground truth)
├── summary            (LLM-generated text)
├── predicted_at
└── created_at
