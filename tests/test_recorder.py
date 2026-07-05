"""Tests for src/recorder.py — Twilio recording fetch/download (Phase 06, FR9)."""
from types import SimpleNamespace

import recorder


class FakeRecordings:
    def __init__(self, sids):
        self._sids = sids

    def list(self, call_sid=None, limit=1):
        return [SimpleNamespace(sid=s) for s in self._sids][:limit]


class FakeClient:
    def __init__(self, sids):
        self.recordings = FakeRecordings(sids)


class TestRecordingUrl:
    def test_builds_mp3_url(self):
        url = recorder.build_recording_url("AC123", "RE456")
        assert url == "https://api.twilio.com/2010-04-01/Accounts/AC123/Recordings/RE456.mp3"


class TestFetchRecordingSid:
    def test_returns_first_sid(self):
        assert recorder.fetch_recording_sid(FakeClient(["RE1", "RE2"]), "CA9") == "RE1"

    def test_none_when_no_recording(self):
        assert recorder.fetch_recording_sid(FakeClient([]), "CA9") is None


class TestSaveRecording:
    def test_downloads_and_writes_mp3(self, tmp_path):
        got = {}

        def fake_http_get(url, auth):
            got["url"] = url
            got["auth"] = auth
            return b"FAKE_MP3_BYTES"

        dest = tmp_path / "call_09" / "recording.mp3"
        ok = recorder.save_recording(
            FakeClient(["RE1"]), "CA9", dest,
            account_sid="AC123", auth_token="tok", http_get=fake_http_get,
        )
        assert ok is True
        assert dest.read_bytes() == b"FAKE_MP3_BYTES"
        assert got["url"].endswith("/Recordings/RE1.mp3")
        assert got["auth"] == ("AC123", "tok")

    def test_returns_false_when_no_recording(self, tmp_path):
        dest = tmp_path / "call_09" / "recording.mp3"
        ok = recorder.save_recording(
            FakeClient([]), "CA9", dest,
            account_sid="AC123", auth_token="tok", http_get=lambda u, a: b"x", retries=1, delay=0,
        )
        assert ok is False
        assert not dest.exists()


class TestFetchMissingRecordings:
    def _make_call(self, root, call_id, meta):
        import utils
        folder = root / call_id
        folder.mkdir(parents=True)
        utils.write_json(folder / "metadata.json", meta)
        return folder

    def test_downloads_only_missing(self, tmp_path):
        # call_a: missing recording + has call_sid -> should download
        self._make_call(tmp_path, "call_a", {"recording_file": None, "call_sid": "CA_A"})
        # call_b: already has recording -> untouched
        self._make_call(tmp_path, "call_b", {"recording_file": "recording.mp3", "call_sid": "CA_B"})
        # call_c: missing but no call_sid -> skipped
        self._make_call(tmp_path, "call_c", {"recording_file": None, "call_sid": None})

        count = recorder.fetch_missing_recordings(
            str(tmp_path), FakeClient(["RE1"]),
            account_sid="AC123", auth_token="tok",
            http_get=lambda u, a: b"MP3", retries=1, delay=0,
        )
        assert count == 1
        assert (tmp_path / "call_a" / "recording.mp3").read_bytes() == b"MP3"
        import utils
        assert utils.read_json(tmp_path / "call_a" / "metadata.json")["recording_file"] == "recording.mp3"
        assert not (tmp_path / "call_c" / "recording.mp3").exists()
