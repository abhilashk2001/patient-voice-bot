"""Tests for src/utils.py — small helpers (Phase 01)."""
import json

import pytest

import utils


class TestNormalizePhone:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("+18054398008", "+18054398008"),
            ("+1-805-439-8008", "+18054398008"),
            ("+1 805 439 8008", "+18054398008"),
            ("  +1 (805) 439-8008  ", "+18054398008"),
            ("+1.805.439.8008", "+18054398008"),
            ("(805) 439-8008", "8054398008"),
        ],
    )
    def test_strips_formatting(self, raw, expected):
        assert utils.normalize_phone(raw) == expected

    def test_preserves_leading_plus(self):
        assert utils.normalize_phone("+1 805 439 8008").startswith("+")

    def test_empty_string_returns_empty(self):
        assert utils.normalize_phone("") == ""


class TestEnsureDir:
    def test_creates_directory(self, tmp_path):
        target = tmp_path / "calls" / "call_01"
        result = utils.ensure_dir(target)
        assert target.is_dir()
        # returns the path it created
        assert str(result) == str(target)

    def test_idempotent(self, tmp_path):
        target = tmp_path / "docs"
        utils.ensure_dir(target)
        # second call must not raise
        utils.ensure_dir(target)
        assert target.is_dir()


class TestJson:
    def test_write_then_read_roundtrip(self, tmp_path):
        path = tmp_path / "meta.json"
        data = {"call_id": "call_09", "duration_seconds": 154, "bugs": ["BUG-001"]}
        utils.write_json(path, data)
        assert path.is_file()
        assert utils.read_json(path) == data

    def test_write_json_creates_parent_dirs(self, tmp_path):
        path = tmp_path / "calls" / "call_02" / "metadata.json"
        utils.write_json(path, {"ok": True})
        assert path.is_file()

    def test_write_json_is_readable_text(self, tmp_path):
        path = tmp_path / "x.json"
        utils.write_json(path, {"a": 1})
        # valid JSON on disk
        assert json.loads(path.read_text())["a"] == 1


class TestFormatTimestamp:
    @pytest.mark.parametrize(
        "seconds,expected",
        [
            (0, "00:00"),
            (5, "00:05"),
            (65, "01:05"),
            (154, "02:34"),
            (600, "10:00"),
            (59, "00:59"),
        ],
    )
    def test_mm_ss(self, seconds, expected):
        assert utils.format_timestamp(seconds) == expected

    def test_accepts_float(self):
        assert utils.format_timestamp(65.9) == "01:05"
