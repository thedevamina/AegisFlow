# ADR-002: Definition of "risky PR" (proxy label)

## Status
Accepted

## Context
There's no ground-truth "this PR was risky" label in GitHub data — we need a
proxy label built from observable signals (reverts, hotfixes, linked bugs).
This label is the target variable for every model in the project, so its
definition must be precise and reproducible, not just "PRs that seem bad."

## Decision
A merged PR is labeled **risky (1)** if ANY of the following hold, checked
within a fixed observation window of **14 days after merge**:
1. The PR was reverted (a later commit/PR with "revert" in the title or
   message references this PR's merge commit SHA).
2. A commit was merged within the window whose message contains "hotfix",
   "fix", or "patch" AND touches >50% of the same files as the original PR.
3. An issue was opened within the window, labeled `bug`, and its body or a
   linked comment references this PR's number.

All other merged PRs are labeled **not risky (0)**.

## Edge cases (explicitly decided, not left ambiguous)
- **Revert after the 14-day window**: NOT counted as risky. Window is fixed
  to keep the label reproducible and comparable across PRs of different ages.
- **Revert by someone other than the original author**: still counts —
  cause of revert matters more than who reverted it.
- **PR reverted then re-merged (revert of a revert)**: original PR still
  labeled risky — it still caused a revert event, regardless of what
  happened after.
- **Draft PRs / PRs closed without merging**: excluded from the dataset
  entirely — label is only defined for merged PRs.
- **Multiple qualifying signals on one PR**: still just a binary label (1),
  not weighted — this is a first-pass proxy, not a severity score.

## Consequences
**Positive:** reproducible, auditable, computable purely from GitHub API
data (no manual labeling needed).

**Negative:** proxy labels are noisy — a PR can be "risky" by this
definition for reasons unrelated to code quality (e.g. a flaky test
triggering a hotfix-labeled commit). This is a known limitation, documented
here rather than discovered later during evaluation.

## Alternatives considered
- **Manual labeling of a sample**: more accurate but not scalable to
  40-60 repos in the timeframe; may revisit as a validation spot-check
  (see Phase 1 Definition of Done — 10 manually reviewed PRs).
- **Longer window (30/90 days)**: rejected as primary definition — dilutes
  the causal link between PR and consequence the longer the window gets;
  kept 14 days as the tighter, more defensible signal.
