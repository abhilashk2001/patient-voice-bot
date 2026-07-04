"""Tests for src/config.py — env loading + authorized-number guard (Phase 01, FR1)."""
import pytest

import config


def base_env(**overrides):
    """A minimal valid environment mapping; override individual keys per test."""
    env = {
        "TARGET_PHONE_NUMBER": "+18054398008",
        "CALLER_PHONE_NUMBER": "+13334445555",
        "OPENAI_API_KEY": "sk-test",
        "OPENAI_REALTIME_MODEL": "gpt-realtime",
        "CALL_OUTPUT_DIR": "./calls",
        "SCENARIOS_FILE": "./scenarios/scenarios.json",
        "MAX_CALL_SECONDS": "180",
        "RECENT_TURNS_LIMIT": "6",
        "DRY_RUN": "false",
    }
    env.update(overrides)
    return env


class TestAuthorizedTargetConstant:
    def test_authorized_target_value(self):
        assert config.AUTHORIZED_TARGET == "+18054398008"


class TestValidateTargetNumber:
    @pytest.mark.parametrize(
        "raw",
        ["+18054398008", "+1-805-439-8008", "+1 805 439 8008", "  +1 (805) 439-8008 "],
    )
    def test_authorized_variants_normalize_and_pass(self, raw):
        assert config.validate_target_number(raw) == "+18054398008"

    @pytest.mark.parametrize("raw", ["+13334445555", "+1-999-999-9999", "8054398008"])
    def test_unauthorized_number_refused(self, raw):
        with pytest.raises(config.UnauthorizedTargetError):
            config.validate_target_number(raw)

    @pytest.mark.parametrize("raw", ["", "   ", None])
    def test_missing_number_raises(self, raw):
        with pytest.raises(config.MissingConfigError):
            config.validate_target_number(raw)


class TestLoadConfig:
    def test_loads_valid_env(self):
        cfg = config.load_config(base_env())
        assert cfg.target_phone_number == "+18054398008"
        assert cfg.caller_phone_number == "+13334445555"
        assert cfg.max_call_seconds == 180
        assert cfg.recent_turns_limit == 6
        assert cfg.dry_run is False

    def test_refuses_unauthorized_target_before_anything_else(self):
        with pytest.raises(config.UnauthorizedTargetError):
            config.load_config(base_env(TARGET_PHONE_NUMBER="+13334445555"))

    def test_missing_required_key_raises(self):
        env = base_env()
        del env["OPENAI_API_KEY"]
        with pytest.raises(config.MissingConfigError):
            config.load_config(env)

    def test_dry_run_truthy_parsing(self):
        assert config.load_config(base_env(DRY_RUN="true")).dry_run is True
        assert config.load_config(base_env(DRY_RUN="false")).dry_run is False

    def test_numeric_fields_are_ints(self):
        cfg = config.load_config(base_env(MAX_CALL_SECONDS="90", RECENT_TURNS_LIMIT="4"))
        assert cfg.max_call_seconds == 90
        assert cfg.recent_turns_limit == 4
