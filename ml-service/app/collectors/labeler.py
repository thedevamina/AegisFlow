"""
Risky-PR labeler implementing ADR-002.
"""
from __future__ import annotations
from datetime import timedelta
from dateutil import parser as dtparser

WINDOW_DAYS = 14
HOTFIX_KEYWORDS = ("hotfix", "fix", "patch")

def is_reverted(pr: dict, all_commits: list[dict]) -> bool:
    merge_sha = pr.get("merge_commit_sha")
    if not merge_sha:
        return False
    merged_at = dtparser.parse(pr["merged_at"]) if pr.get("merged_at") else None
    if not merged_at:
        return False
    window_end = merged_at + timedelta(days=WINDOW_DAYS)
    for c in all_commits:
        msg = c["commit"]["message"].lower()
        commit_date = dtparser.parse(c["commit"]["author"]["date"])
        if merged_at <= commit_date <= window_end:
            if "revert" in msg and merge_sha[:7] in msg:
                return True
    return False

def has_hotfix_followup(pr: dict, pr_files: list[str], all_commits: list[dict]) -> bool:
    merged_at = dtparser.parse(pr["merged_at"]) if pr.get("merged_at") else None
    if not merged_at or not pr_files:
        return False
    window_end = merged_at + timedelta(days=WINDOW_DAYS)
    pr_file_set = set(pr_files)
    for c in all_commits:
        msg = c["commit"]["message"].lower()
        commit_date = dtparser.parse(c["commit"]["author"]["date"])
        if merged_at <= commit_date <= window_end and any(k in msg for k in HOTFIX_KEYWORDS):
            commit_files = set(f["filename"] for f in c.get("files", []))
            if commit_files and len(commit_files & pr_file_set) / len(pr_file_set) > 0.5:
                return True
    return False

def is_bug_linked(pr: dict, issues: list[dict]) -> bool:
    merged_at = dtparser.parse(pr["merged_at"]) if pr.get("merged_at") else None
    if not merged_at:
        return False
    window_end = merged_at + timedelta(days=WINDOW_DAYS)
    pr_number = str(pr["number"])
    for issue in issues:
        labels = [l["name"] for l in issue.get("labels", [])]
        if "bug" not in labels:
            continue
        created = dtparser.parse(issue["created_at"])
        if merged_at <= created <= window_end:
            body = (issue.get("body") or "")
            if pr_number in body:
                return True
    return False

def label_pr(pr: dict, pr_files: list[str], all_commits: list[dict], issues: list[dict]) -> dict:
    if pr.get("state") != "closed" or not pr.get("merged_at"):
        return {"is_risky": None, "risk_reason": None}

    if is_reverted(pr, all_commits):
        return {"is_risky": True, "risk_reason": "reverted"}
    if has_hotfix_followup(pr, pr_files, all_commits):
        return {"is_risky": True, "risk_reason": "hotfix_followup"}
    if is_bug_linked(pr, issues):
        return {"is_risky": True, "risk_reason": "bug_linked"}
    return {"is_risky": False, "risk_reason": None}
