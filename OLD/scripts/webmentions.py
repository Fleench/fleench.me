"""Webmention plugin + publish command in one file."""
from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import urllib.error
import urllib.parse
import urllib.request

LOGGER = logging.getLogger("gen")
WEBMENTION_STATE_PATH = Path(".webmention-state.json")
FED_BRIDGY_ENDPOINT = "https://fed.brid.gy/webmention"


def _extract_links_from_markdown(markdown_text: str) -> set[str]:
    links = set(re.findall(r"\[[^\]]+\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", markdown_text))
    links.update(re.findall(r"<((?:https?://)[^>]+)>", markdown_text))
    return {link.strip() for link in links if link.strip()}


def _extract_links_from_html(html_text: str) -> set[str]:
    links = set(re.findall(r"(?:href|src)=['\"]([^'\"]+)['\"]", html_text))
    return {link.strip() for link in links if link.strip()}


def _is_http_external(link: str, site_host: str) -> bool:
    parsed = urllib.parse.urlparse(link)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    return parsed.netloc != site_host


def _normalize_for_hash(content: str) -> str:
    return " ".join(content.split())


def _source_fingerprint(content: str) -> str:
    normalized = _normalize_for_hash(content)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _load_webmention_state() -> dict[str, Any]:
    if not WEBMENTION_STATE_PATH.exists():
        return {"version": 1, "queue": [], "published": [], "current_links": {}}
    try:
        data = json.loads(WEBMENTION_STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"version": 1, "queue": [], "published": [], "current_links": {}}
    if not isinstance(data, dict):
        return {"version": 1, "queue": [], "published": [], "current_links": {}}
    data.setdefault("version", 1)
    data.setdefault("queue", [])
    data.setdefault("published", [])
    data.setdefault("current_links", {})
    return data


def _save_webmention_state(state: dict[str, Any]) -> None:
    WEBMENTION_STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def discover_main(_src_dir: Path, _out_dir: Path, config: dict[str, Any], all_pages: list[Any]) -> None:
    site_url = str(config.get("site_url", "https://flench.me"))
    site_host = urllib.parse.urlparse(site_url).netloc
    if not site_host:
        return

    discovered: dict[tuple[str, str], str] = {}
    current_links: dict[str, set[str]] = {}

    def record_discovery(source: str, target: str, source_hash: str) -> None:
        discovered.setdefault((source, target), source_hash)
        current_links.setdefault(source, set()).add(target)

    def removed_source_hash(source: str, targets: set[str]) -> str:
        return _source_fingerprint(f"{source}\nremoved\n" + "\n".join(sorted(targets)))

    for page in all_pages:
        source = f"{site_url.rstrip('/')}{page.rel_url}"
        markdown_hash = _source_fingerprint(page.parsed.body)
        for link in _extract_links_from_markdown(page.parsed.body):
            if _is_http_external(link, site_host):
                record_discovery(source, link, markdown_hash)

        html_hash = _source_fingerprint(page.rendered_html)
        for link in _extract_links_from_html(page.rendered_html):
            if _is_http_external(link, site_host):
                record_discovery(source, link, html_hash)

    state = _load_webmention_state()
    queue = [item for item in state.get("queue", []) if isinstance(item, dict)]
    published = [item for item in state.get("published", []) if isinstance(item, dict)]
    previous_current_links_raw = state.get("current_links", {})

    previous_current_links: dict[str, set[str]] = {}
    if isinstance(previous_current_links_raw, dict):
        for source, targets in previous_current_links_raw.items():
            if isinstance(source, str) and isinstance(targets, list):
                previous_current_links[source] = {str(target).strip() for target in targets if str(target).strip()}

    existing = {
        (
            str(item.get("source", "")).strip(),
            str(item.get("target", "")).strip(),
            str(item.get("source_hash", "")).strip(),
            str(item.get("event", "added") or "added").strip(),
        )
        for item in [*queue, *published]
    }

    queued_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for (source, target), source_hash in sorted(discovered.items()):
        key = (source, target, source_hash, "added")
        if key in existing:
            continue
        queue.append({"source": source, "target": target, "source_hash": source_hash, "event": "added", "queued_at": queued_at})
        existing.add(key)

    for source, previous_targets in previous_current_links.items():
        removed_targets = previous_targets - current_links.get(source, set())
        if not removed_targets:
            continue
        removal_hash = removed_source_hash(source, removed_targets)
        for target in sorted(removed_targets):
            key = (source, target, removal_hash, "removed")
            if key in existing:
                continue
            queue.append({"source": source, "target": target, "source_hash": removal_hash, "event": "removed", "queued_at": queued_at})
            existing.add(key)

    state["queue"] = queue
    state["current_links"] = {source: sorted(targets) for source, targets in sorted(current_links.items())}
    _save_webmention_state(state)


def _send_webmention(source: str, target: str) -> None:
    payload = urllib.parse.urlencode({"source": source, "target": target}).encode("utf-8")
    request = urllib.request.Request(FED_BRIDGY_ENDPOINT, data=payload, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(request, timeout=15):
        return


def publish_main(config: dict[str, Any]) -> None:
    dry_run = str(config.get("dry_run", "")).strip().lower() in {"1", "true", "yes", "on"}
    state = _load_webmention_state()
    queue = [item for item in state.get("queue", []) if isinstance(item, dict)]
    published = [item for item in state.get("published", []) if isinstance(item, dict)]

    remaining: list[dict[str, Any]] = []
    sent = 0
    failed = 0
    for item in queue:
        source = str(item.get("source", "")).strip()
        target = str(item.get("target", "")).strip()
        if not source or not target:
            continue
        if dry_run:
            LOGGER.info("DRY RUN publish %s -> %s", source, target)
            remaining.append(item)
            continue
        try:
            _send_webmention(source, target)
            sent += 1
            published.append({**item, "published_at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
        except urllib.error.URLError as exc:
            failed += 1
            remaining.append(item)
            LOGGER.error("Failed publishing %s -> %s: %s", source, target, exc)

    state["queue"] = remaining
    state["published"] = published
    _save_webmention_state(state)
    LOGGER.info("Published %s webmention(s); %s failed", sent, failed)


def main(*args: Any) -> None:
    if len(args) == 1 and isinstance(args[0], dict):
        publish_main(args[0])
        return
    if len(args) == 4:
        discover_main(args[0], args[1], args[2], args[3])
        return
    raise TypeError("webmentions.main expects either (config) or (src_dir, out_dir, config, all_pages)")
