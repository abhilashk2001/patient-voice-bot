"""Tests for src/artifacts.py — metadata + per-call artifact saving (Phase 06, FR11)."""
import artifacts
import utils


SCENARIO = {
    "call_id": "call_09",
    "scenario_name": "Off-topic math drift",
    "persona": "Curious young adult with elbow pain",
}


def sample_state():
    return {
        "call_id": "call_09",
        "scenario_name": "Off-topic math drift",
        "duration_seconds": 154,
        "outcome": "Assistant answered off-topic math",
        "turns": [("assistant", "Hello"), ("patient", "Hi, what's 8 plus 9?")],
    }


class TestBuildMetadata:
    def test_required_fields(self):
        m = artifacts.build_metadata(
            SCENARIO, sample_state(), start_time="2026-07-04T16:00:00", recording_file="recording.mp3"
        )
        assert m["call_id"] == "call_09"
        assert m["scenario_name"] == "Off-topic math drift"
        assert m["start_time"] == "2026-07-04T16:00:00"
        assert m["duration_seconds"] == 154
        assert m["recording_file"] == "recording.mp3"
        assert m["transcript_file"] == "transcript.txt"
        assert m["scenario_file"] == "scenario.json"
        assert m["outcome"] == "Assistant answered off-topic math"
        assert m["bugs_found"] == []
        assert "call_quality_notes" in m

    def test_recording_file_none_when_missing(self):
        m = artifacts.build_metadata(SCENARIO, sample_state(), start_time="t", recording_file=None)
        assert m["recording_file"] is None


class TestSaveArtifacts:
    def test_writes_all_files(self, tmp_path):
        folder = artifacts.save_artifacts(
            SCENARIO, sample_state(), str(tmp_path), start_time="2026-07-04T16:00:00", recording_file="recording.mp3"
        )
        assert (folder / "transcript.txt").is_file()
        assert (folder / "scenario.json").is_file()
        assert (folder / "metadata.json").is_file()

    def test_folder_named_by_call_id(self, tmp_path):
        folder = artifacts.save_artifacts(SCENARIO, sample_state(), str(tmp_path), start_time="t")
        assert folder.name == "call_09"

    def test_scenario_snapshot_matches(self, tmp_path):
        folder = artifacts.save_artifacts(SCENARIO, sample_state(), str(tmp_path), start_time="t")
        assert utils.read_json(folder / "scenario.json")["call_id"] == "call_09"

    def test_metadata_is_valid_json_with_outcome(self, tmp_path):
        folder = artifacts.save_artifacts(SCENARIO, sample_state(), str(tmp_path), start_time="t")
        meta = utils.read_json(folder / "metadata.json")
        assert meta["outcome"] == "Assistant answered off-topic math"

    def test_transcript_contains_both_sides(self, tmp_path):
        folder = artifacts.save_artifacts(SCENARIO, sample_state(), str(tmp_path), start_time="t")
        text = (folder / "transcript.txt").read_text()
        assert "Assistant:" in text and "Patient:" in text
