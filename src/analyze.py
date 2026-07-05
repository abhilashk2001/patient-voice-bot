"""AI-assisted bug-candidate drafter (Phase 09).

Scans each saved call against its scenario's ``bug_indicators`` and emits draft
candidate entries to BUG_CANDIDATES.md. This does NOT auto-publish bugs — a human
reviews, culls, and rewrites the strong ones into BUG_REPORT.md (PRD anti-pattern:
fully automated bug reporting). It just pre-fills evidence to speed curation.
"""
import sys
from pathlib import Path
from typing import Any, Dict, List

from utils import read_json


def find_snippets(transcript_text: str, keywords: List[str]) -> List[str]:
    """Return transcript lines containing any of ``keywords`` (case-insensitive)."""
    hits = []
    for line in transcript_text.splitlines():
        low = line.lower()
        if any(k.lower() in low for k in keywords):
            hits.append(line.strip())
    return hits


def detect_math_answered(transcript_text: str) -> List[str]:
    """Flag assistant turns that answer arithmetic (scope-control failure)."""
    hits = []
    for line in transcript_text.splitlines():
        low = line.strip().lower()
        if low.startswith("assistant:") and "plus" in low and any(c.isdigit() for c in line):
            hits.append(line.strip())
    return hits


def draft_candidate(scenario: Dict[str, Any], transcript_text: str, metadata: Dict[str, Any]) -> str:
    """Draft one candidate block for a call: indicators + auto-flagged evidence."""
    lines = [
        f"## CANDIDATE — {scenario.get('call_id')}: {scenario.get('scenario_name')}",
        f"Outcome: {metadata.get('outcome')}",
        "",
        "Bug indicators to check:",
    ]
    lines += [f"- [ ] {ind}" for ind in scenario.get("bug_indicators", [])]

    math = detect_math_answered(transcript_text)
    if math:
        lines += ["", "Auto-flagged — assistant answered off-topic math:"]
        lines += [f"  - {m}" for m in math]

    lines += ["", "_Confirm/cull, set severity, and write why-it-matters in BUG_REPORT.md._", ""]
    return "\n".join(lines)


def build_candidates(calls_dir: str) -> str:
    """Build the full BUG_CANDIDATES.md text from all saved call folders."""
    blocks = ["# Bug Candidates (AI-drafted — review before promoting to BUG_REPORT.md)", ""]
    for scen_path in sorted(Path(calls_dir).glob("*/scenario.json")):
        folder = scen_path.parent
        scenario = read_json(scen_path)
        transcript = (folder / "transcript.txt").read_text() if (folder / "transcript.txt").exists() else ""
        metadata = read_json(folder / "metadata.json") if (folder / "metadata.json").exists() else {}
        blocks.append(draft_candidate(scenario, transcript, metadata))
    return "\n".join(blocks)


if __name__ == "__main__":  # pragma: no cover
    calls_dir = sys.argv[1] if len(sys.argv) > 1 else "./calls"
    out = Path("BUG_CANDIDATES.md")
    out.write_text(build_candidates(calls_dir))
    print(f"Wrote {out}")
