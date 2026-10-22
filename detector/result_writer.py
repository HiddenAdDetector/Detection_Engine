"""Strict writer for the contest's ``result.json`` interchange format."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

from .models import Verdict

TOPIC = "TOPIC"
KST = timezone(timedelta(hours=9))
ALLOWED_TECHNIQUES = frozenset({"HOMOGLYPH", "JAMO", "TRANSPARENT", "OFFSCREEN"})


def _as_kst(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=KST)
    return value.astimezone(KST)


def _comparison_url(url: str) -> tuple[str, str, tuple[tuple[str, str], ...]]:
    """Build the PDF-specified URL deduplication key."""

    parsed = urlsplit(url)
    path = parsed.path.rstrip("/")
    query = tuple(sorted(parse_qsl(parsed.query, keep_blank_values=True), key=lambda item: item[0]))
    return parsed.netloc.casefold(), path, query


def _finding_location(verdict: Verdict) -> str:
    frames = [f'iframe[src="{source}"]' for source in verdict.frame_path]
    return " >>> ".join([*frames, verdict.location])


def _default_output_dir() -> Path:
    executable_or_script = sys.executable if getattr(sys, "frozen", False) else sys.argv[0]
    return Path(executable_or_script).resolve().parent


def write_result(
    entry_url: str,
    started_at: datetime,
    finished_at: datetime,
    verdicts: list[Verdict],
    out_dir: str | Path | None = None,
    tool_version: str = "",
    topic: str = TOPIC,
) -> Path:
    """Write a schema-strict result file and return its absolute path.

    The function accepts an incomplete list of verdicts, so callers can invoke
    it from cancellation and timeout handlers without a separate code path.
    """

    started = _as_kst(started_at)
    finished = _as_kst(finished_at)
    elapsed = round((finished - started).total_seconds(), 3)
    elapsed_value: int | float = int(elapsed) if elapsed.is_integer() else elapsed

    findings: list[dict[str, object]] = []
    seen: set[tuple[tuple[str, str, tuple[tuple[str, str], ...]], str, str]] = set()
    for verdict in verdicts:
        if not verdict.is_violation:
            continue
        location = _finding_location(verdict)
        for technique in dict.fromkeys(verdict.techniques):
            if technique not in ALLOWED_TECHNIQUES:
                raise ValueError(f"Unsupported result technique: {technique!r}")
            dedup_key = (_comparison_url(verdict.url), location, technique)
            if dedup_key in seen:
                continue
            seen.add(dedup_key)
            findings.append(
                {
                    "id": f"f_{len(findings) + 1:03d}",
                    "url": verdict.url,
                    "is_violation": True,
                    "location": location,
                    "evidence_text": verdict.original_text,
                    "technique": technique,
                }
            )

    payload = {
        "meta": {
            "topic": topic,
            "entry_url": entry_url,
            "started_at": started.isoformat(timespec="seconds"),
            "finished_at": finished.isoformat(timespec="seconds"),
            "elapsed_sec": elapsed_value,
            "tool_version": tool_version,
        },
        "findings": findings,
    }

    destination = Path(out_dir) if out_dir is not None else _default_output_dir()
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    result_path = destination / "result.json"
    temporary_path = destination / ".result.json.tmp"
    with temporary_path.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    temporary_path.replace(result_path)
    return result_path
