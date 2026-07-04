"""Tests for src/call_runner.py — the mockable pre-flight guard (Phase 04).

The async bridge loop itself is verified manually on a live call; here we test
the deterministic fail-fast that prevents dialing without complete config.
"""
import pytest

import call_runner
import config as config_mod


def full_env(**over):
    env = {
        "TARGET_PHONE_NUMBER": "+18054398008",
        "CALLER_PHONE_NUMBER": "+13334445555",
        "OPENAI_API_KEY": "sk-test",
        "OPENAI_REALTIME_MODEL": "gpt-realtime",
        "CALL_OUTPUT_DIR": "./calls",
        "SCENARIOS_FILE": "scenarios/scenarios.json",
        "MAX_CALL_SECONDS": "180",
        "RECENT_TURNS_LIMIT": "6",
        "DRY_RUN": "false",
        "TWILIO_ACCOUNT_SID": "AC123",
        "TWILIO_AUTH_TOKEN": "tok",
        "TWILIO_PHONE_NUMBER": "+15551230000",
        "PUBLIC_MEDIA_STREAM_URL": "wss://abc.ngrok-free.app/media",
    }
    env.update(over)
    return env


class TestValidateReadyForCall:
    def test_complete_config_passes(self):
        cfg = config_mod.load_config(full_env())
        call_runner.validate_ready_for_call(cfg)  # no raise

    @pytest.mark.parametrize(
        "missing_key",
        ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER", "PUBLIC_MEDIA_STREAM_URL"],
    )
    def test_missing_telephony_field_raises(self, missing_key):
        cfg = config_mod.load_config(full_env(**{missing_key: ""}))
        with pytest.raises(config_mod.MissingConfigError):
            call_runner.validate_ready_for_call(cfg)

    def test_error_names_telephony(self):
        cfg = config_mod.load_config(full_env(PUBLIC_MEDIA_STREAM_URL=""))
        with pytest.raises(config_mod.MissingConfigError) as ei:
            call_runner.validate_ready_for_call(cfg)
        assert "telephony" in str(ei.value).lower()
