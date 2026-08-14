"""
GitHub data collector for NEXUS.
Pagination + rate-limit handling + disk caching built in from day one.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger("nexus.collector")
logging.basicConfig(level=logging.INFO)

GITHUB_API = "https://api.github.com"
CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL_SECONDS = 60 * 60 * 6  # 6 hours


class RateLimitExceeded(Exception):
    pass


@dataclass
class RateLimitInfo:
    remaining: int
    reset_at: int

    @classmethod
    def from_headers(cls, headers: dict) -> "RateLimitInfo":
        return cls(
            remaining=int(headers.get("X-RateLimit-Remaining", 1)),
            reset_at=int(headers.get("X-RateLimit-Reset", time.time() + 60)),
        )


class DiskCache:
    def __init__(self, cache_dir: Path = CACHE_DIR, ttl: int = CACHE_TTL_SECONDS):
        self.cache_dir = cache_dir
        self.ttl = ttl

    def _key(self, url: str, params: dict | None) -> str:
        raw = url + json.dumps(params or {}, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, url: str, params: dict | None) -> Any | None:
        path = self.cache_dir / f"{self._key(url, params)}.json"
        if not path.exists():
            return None
        if time.time() - path.stat().st_mtime > self.ttl:
            return None
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            return None

    def set(self, url: str, params: dict | None, data: Any) -> None:
        path = self.cache_dir / f"{self._key(url, params)}.json"
        path.write_text(json.dumps(data))


class GitHubCollector:
    def __init__(self, token: str | None = None, cache: DiskCache | None = None):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.session = requests.Session()
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        self.session.headers.update(headers)
        self.cache = cache or DiskCache()

    @retry(
        reraise=True,
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=1, max=20),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
    )
    def _get(self, url: str, params: dict | None = None, use_cache: bool = True) -> tuple[Any, dict]:
        if use_cache:
            cached = self.cache.get(url, params)
            if cached is not None:
                logger.debug("cache hit: %s %s", url, params)
                return cached, {}

        resp = self.session.get(url, params=params, timeout=15)

        if resp.status_code == 403 and "rate limit" in resp.text.lower():
            rl = RateLimitInfo.from_headers(resp.headers)
            wait_s = max(rl.reset_at - int(time.time()), 1)
            if wait_s > 120:
                raise RateLimitExceeded(f"Rate limited; reset in {wait_s}s -- aborting run")
            logger.warning("Rate limited. Sleeping %ss until reset.", wait_s)
            time.sleep(wait_s + 1)
            resp = self.session.get(url, params=params, timeout=15)

        resp.raise_for_status()
        data = resp.json()

        if use_cache:
            self.cache.set(url, params, data)

        return data, dict(resp.headers)

    def _paginate(self, url: str, params: dict | None = None, max_items: int | None = None) -> Iterator[dict]:
        params = dict(params or {})
        params.setdefault("per_page", 100)
        page = 1
        yielded = 0

        while True:
            params["page"] = page
            data, _ = self._get(url, params=params)
            if not data:
                break
            for item in data:
                yield item
                yielded += 1
                if max_items and yielded >= max_items:
                    return
            if len(data) < params["per_page"]:
                break
            page += 1

    def get_pull_requests(self, repo: str, state: str = "closed", max_items: int = 200) -> list[dict]:
        url = f"{GITHUB_API}/repos/{repo}/pulls"
        params = {"state": state, "sort": "updated", "direction": "desc"}
        prs = list(self._paginate(url, params=params, max_items=max_items))
        logger.info("Collected %d PRs from %s", len(prs), repo)
        return prs

    def get_pr_files(self, repo: str, pr_number: int) -> list[dict]:
        url = f"{GITHUB_API}/repos/{repo}/pulls/{pr_number}/files"
        return list(self._paginate(url, max_items=300))

    def get_issues(self, repo: str, state: str = "all", labels: str | None = None, max_items: int = 300) -> list[dict]:
        url = f"{GITHUB_API}/repos/{repo}/issues"
        params = {"state": state}
        if labels:
            params["labels"] = labels
        issues = list(self._paginate(url, params=params, max_items=max_items))
        return [i for i in issues if "pull_request" not in i]

    def get_commits(self, repo: str, max_items: int = 300) -> list[dict]:
        url = f"{GITHUB_API}/repos/{repo}/commits"
        return list(self._paginate(url, max_items=max_items))

    def rate_limit_status(self) -> dict:
        data, _ = self._get(f"{GITHUB_API}/rate_limit", use_cache=False)
        return data