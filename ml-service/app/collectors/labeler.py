"""
Risky-PR labeler implementing ADR-002 (revised v2).
"""
from __future__ import annotations
import re
from datetime import timedelta
from dateutil import parser as dtparser

WINDOW_DAYS = 14


def is_reverted(pr: dict, all_commits: list[dict]) -> bool:
    """GitHub's default revert commit message references the PR number or
    title in parentheses, e.g. Revert "Fix typo" (#1234) -- NOT the SHA."""
    merged_at = dtparser.parse(pr["merged_at"]) if pr.get("merged_at") else None
    if not merged_at:
        return False
    window_end = merged_at + timedelta(days=WINDOW_DAYS)
    pr_number_pattern = re.compile(rf"#{pr['number']}(?!\d)")

    for c in all_commits:
        msg = c["commit"]["message"].lower()
        commit_date = dtparser.parse(c["commit"]["author"]["date"])
        if merged_at <= commit_date <= window_end:
            if msg.startswith("revert") and pr_number_pattern.search(msg):
                return True
    return False


def has_hotfix_followup(pr: dict, pr_files: list[str], all_commits: list[dict]) -> bool:
    """Proxy signal: a commit within the window that explicitly says 'hotfix'
    AND references this PR's number."""
    merged_at = dtparser.parse(pr["merged_at"]) if pr.get("merged_at") else None
    if not merged_at:
        return False
    window_end = merged_at + timedelta(days=WINDOW_DAYS)
    pr_number_pattern = re.compile(rf"#{pr['number']}(?!\d)")

    for c in all_commits:
        msg = c["commit"]["message"].lower()
        commit_date = dtparser.parse(c["commit"]["author"]["date"])
        if merged_at <= commit_date <= window_end:
            if "hotfix" in msg and pr_number_pattern.search(msg):
                return True
    return False


def is_bug_linked(pr: dict, issues: list[dict]) -> bool:
    """FIXED DIRECTION: check the PR's own body for references to a
    bug-labeled issue (e.g. 'Fixes #123'). The original version checked
    whether an issue's body referenced the PR -- backwards; that almost
    never happens on GitHub, which is why it never matched."""
    pr_body = (pr.get("body") or "").lower()
    if not pr_body:
        return False

    bug_issue_numbers = {
        issue["number"] for issue in issues
        if "bug" in [l["name"].lower() for l in issue.get("labels", [])]
    }
    if not bug_issue_numbers:
        return False

    referenced = re.findall(r"#(\d+)", pr_body)
    referenced_numbers = {int(n) for n in referenced}

    return bool(bug_issue_numbers & referenced_numbers)


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