"""
Re-label already-collected PRs using per-PR time-windowed commits/issues
(fixes the bug where a repo-wide 'latest 300' sample never covered PRs
merged long before the sample's date range).
"""
import json
from datetime import timedelta
from dateutil import parser as dtparser
from sqlalchemy import text
from app.db import engine
from app.collectors.github_collector import GitHubCollector
from app.collectors.labeler import label_pr, WINDOW_DAYS

collector = GitHubCollector()

with engine.begin() as conn:
    repos = conn.execute(text("SELECT id, full_name FROM repos")).fetchall()

for repo_id, full_name in repos:
    print(f"\n=== Re-labeling {full_name} ===")

    with engine.begin() as conn:
        prs = conn.execute(
            text("SELECT id, raw_payload FROM pull_requests WHERE repo_id = :rid"),
            {"rid": repo_id},
        ).fetchall()

    for pr_id, raw_payload in prs:
        pr = raw_payload if isinstance(raw_payload, dict) else json.loads(raw_payload)

        if pr.get("state") != "closed" or not pr.get("merged_at"):
            continue  # excluded per ADR-002, nothing to fetch

        merged_at = dtparser.parse(pr["merged_at"])
        window_end = merged_at + timedelta(days=WINDOW_DAYS)

        try:
            commits = collector.get_commits_in_range(
                full_name, merged_at.isoformat(), window_end.isoformat()
            )
            issues = collector.get_issues_in_range(full_name, merged_at.isoformat())
            issues = [i for i in issues if "pull_request" not in i]
        except Exception as e:
            print(f"  !! skip PR (id={pr_id}) due to fetch error: {e}")
            continue

        label = label_pr(pr, [], commits, issues)
        if label["is_risky"] is None:
            continue

        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO labels (pull_request_id, is_risky, risk_reason, evaluated_at, created_at, updated_at)
                    VALUES (:pr_id, :is_risky, :risk_reason, NOW(), NOW(), NOW())
                    ON CONFLICT (pull_request_id) DO UPDATE
                        SET is_risky = EXCLUDED.is_risky, risk_reason = EXCLUDED.risk_reason,
                            evaluated_at = NOW(), updated_at = NOW()
                """),
                {"pr_id": pr_id, "is_risky": label["is_risky"], "risk_reason": label["risk_reason"]},
            )
        print(f"  PR (id={pr_id}): risky={label['is_risky']} reason={label['risk_reason']}")

print("\nRe-labeling done.")