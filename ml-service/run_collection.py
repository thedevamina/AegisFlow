"""
Phase 1 pipeline: collect PRs from target repos, label them per ADR-002,
store everything in Postgres.
"""
import time
from app.collectors.github_collector import GitHubCollector
from app.collectors.labeler import label_pr
from app.db import get_or_create_repo, insert_pull_request, insert_files_changed, insert_label

TARGET_REPOS = [
    "psf/requests",
    "pallets/flask",
    "django/django",
]

MAX_PRS_PER_REPO = 20


def process_repo(collector: GitHubCollector, repo: str):
    print(f"\n=== Processing {repo} ===")
    repo_id = get_or_create_repo(repo)

    prs = collector.get_pull_requests(repo, state="closed", max_items=MAX_PRS_PER_REPO)
    print(f"Fetched {len(prs)} PRs")

    all_commits = collector.get_commits(repo, max_items=200)
    issues = collector.get_issues(repo, state="all", max_items=200)

    author_pr_counts: dict[str, int] = {}

    for pr in prs:
        author = pr["user"]["login"]
        author_pr_counts[author] = author_pr_counts.get(author, 0) + 1

        pr_files = collector.get_pr_files(repo, pr["number"])
        filenames = [f["filename"] for f in pr_files]
        test_touched = any("test" in f.lower() for f in filenames)

        pr_id = insert_pull_request(
            repo_id=repo_id,
            pr=pr,
            author_pr_count=author_pr_counts[author],
            test_files_touched=test_touched,
        )
        insert_files_changed(pr_id, pr_files)

        label = label_pr(pr, filenames, all_commits, issues)
        insert_label(pr_id, label["is_risky"], label["risk_reason"])

        print(f"  PR #{pr['number']}: risky={label['is_risky']} reason={label['risk_reason']}")

        time.sleep(0.3)


def main():
    collector = GitHubCollector()
    for repo in TARGET_REPOS:
        process_repo(collector, repo)
    print("\nDone.")


if __name__ == "__main__":
    main()
