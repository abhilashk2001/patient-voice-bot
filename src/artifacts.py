"""Per-call artifact orchestration: metadata + saving the call folder (Phase 06).

Writes transcript.txt, scenario.json, and metadata.json into calls/<call_id>/.
The recording is downloaded separately by ``recorder`` and referenced here.
"""
from pathlib import Path
from typing import Any, Dict, Optional

import transcript_builder
from utils import ensure_dir, write_json


def build_metadata(
    scenario: Dict[str, Any],
    state: Dict[str, Any],
    *,
    start_time: str,
    recording_file: Optional[str] = None,
) -> Dict[str, Any]:
    """Build the metadata.json contents (PRD FR11)."""
    return {
        "call_id": scenario.get("call_id"),
        "scenario_name": scenario.get("scenario_name"),
        "start_time": start_time,
        "duration_seconds": state.get("duration_seconds"),
        "recording_file": recording_file,
        "transcript_file": "transcript.txt",
        "scenario_file": "scenario.json",
        "outcome": state.get("outcome"),
        "bugs_found": [],
        "call_quality_notes": state.get("call_quality_notes", ""),
    }


def save_artifacts(
    scenario: Dict[str, Any],
    state: Dict[str, Any],
    output_root: str,
    *,
    start_time: str,
    recording_file: Optional[str] = None,
) -> Path:
    """Write transcript, scenario snapshot, and metadata to calls/<call_id>/."""
    folder = ensure_dir(Path(output_root) / scenario["call_id"])
    (folder / "transcript.txt").write_text(transcript_builder.build_transcript(scenario, state))
    write_json(folder / "scenario.json", scenario)
    write_json(
        folder / "metadata.json",
        build_metadata(scenario, state, start_time=start_time, recording_file=recording_file),
    )
    return folder
