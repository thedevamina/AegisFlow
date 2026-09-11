import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)


def get_or_create_repo(full_name: str) -> int:
    owner, name = full_name.split("/")
    with engine.begin() as conn:
        result = conn.execute(
            text("SELECT id FROM repos WHERE full_name = :full_name"),
            {"full_name": full_name},
        ).fetchone()
        if result:
            return result[0]
        result = conn.execute(
            text("""
                INSERT INTO repos (full_name, owner, name, collected_at, created_at, updated_at)
                VALUES (:full_name, :owner, :name, NOW(), NOW(), NOW())
                RETURNING id
            """),
            {"full_name": full_name, "owner": owner, "name": name},
        ).fetchone()
        return result[0]


def insert_pull_request(repo_id: int, pr: dict, author_pr_count: int, test_files_touched: bool) -> int:
    import json
    with engine.begin() as conn:
        result = conn.execute(
            text("""
                INSERT INTO pull_requests
                    (repo_id, github_pr_number, title, author_login, author_pr_count,
                     state, created_at_github, merged_at_github, closed_at_github,
                     additions, deletions, changed_files_count, test_files_touched,
                     raw_payload, created_at, updated_at)
                VALUES
                    (:repo_id, :pr_number, :title, :author, :author_pr_count,
                     :state, :created_at, :merged_at, :closed_at,
                     :additions, :deletions, :changed_files, :test_touched,
                     :raw_payload, NOW(), NOW())
                ON CONFLICT (repo_id, github_pr_number) DO UPDATE
                    SET state = EXCLUDED.state, updated_at = NOW()
                RETURNING id
            """),
            {
                "repo_id": repo_id,
                "pr_number": pr["number"],
                "title": pr["title"][:255],
                "author": pr["user"]["login"],
                "author_pr_count": author_pr_count,
                "state": pr["state"],
                "created_at": pr.get("created_at"),
                "merged_at": pr.get("merged_at"),
                "closed_at": pr.get("closed_at"),
                "additions": pr.get("additions", 0) or 0,
                "deletions": pr.get("deletions", 0) or 0,
                "changed_files": pr.get("changed_files", 0) or 0,
                "test_touched": test_files_touched,
                "raw_payload": json.dumps(pr),
            },
        ).fetchone()
        return result[0]


def insert_files_changed(pull_request_id: int, files: list[dict]):
    with engine.begin() as conn:
        for f in files:
            conn.execute(
                text("""
                    INSERT INTO files_changed
                        (pull_request_id, filename, status, additions, deletions, created_at, updated_at)
                    VALUES
                        (:pr_id, :filename, :status, :additions, :deletions, NOW(), NOW())
                """),
                {
                    "pr_id": pull_request_id,
                    "filename": f["filename"],
                    "status": f["status"],
                    "additions": f.get("additions", 0),
                    "deletions": f.get("deletions", 0),
                },
            )


def insert_label(pull_request_id: int, is_risky: bool | None, risk_reason: str | None):
    if is_risky is None:
        return
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO labels (pull_request_id, is_risky, risk_reason, evaluated_at, created_at, updated_at)
                VALUES (:pr_id, :is_risky, :risk_reason, NOW(), NOW(), NOW())
                ON CONFLICT (pull_request_id) DO UPDATE
                    SET is_risky = EXCLUDED.is_risky, risk_reason = EXCLUDED.risk_reason,
                        evaluated_at = NOW(), updated_at = NOW()
            """),
            {"pr_id": pull_request_id, "is_risky": is_risky, "risk_reason": risk_reason},
        )
