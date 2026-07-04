"""Tests for per-scenario Realtime session config (Phase 05)."""
import realtime_bridge as rb
import scenario_loader


def scenarios():
    return scenario_loader.load_scenarios("scenarios/scenarios.json")


class TestBargeIn:
    def test_default_is_polite_patient_yields(self):
        # barge-in off (default): clinic speech interrupts the patient -> polite
        td = rb.build_session_update("x")["session"]["audio"]["input"]["turn_detection"]
        assert td["interrupt_response"] is True

    def test_allow_barge_in_keeps_patient_talking(self):
        td = rb.build_session_update("x", allow_barge_in=True)["session"]["audio"]["input"]["turn_detection"]
        assert td["interrupt_response"] is False


class TestVoiceForScenario:
    def test_explicit_override_wins(self):
        card = {"call_id": "call_02", "realtime_voice": "cedar"}
        assert rb.voice_for_scenario(card, default="alloy") == "cedar"

    def test_deterministic_per_call_id(self):
        a = rb.voice_for_scenario({"call_id": "call_01"}, default="alloy")
        b = rb.voice_for_scenario({"call_id": "call_02"}, default="alloy")
        # stable across calls
        assert a == rb.voice_for_scenario({"call_id": "call_01"}, default="alloy")
        # varied across scenarios (adjacent ids differ)
        assert a != b
        assert a in rb.VOICE_POOL and b in rb.VOICE_POOL

    def test_falls_back_to_pool_not_default_when_no_override(self):
        # varied realism: without override we pick from the pool deterministically
        v = rb.voice_for_scenario({"call_id": "call_05"}, default="alloy")
        assert v in rb.VOICE_POOL


class TestSessionKwargsForScenario:
    class _Cfg:
        realtime_voice = "alloy"

    def test_defaults_from_real_scenario(self):
        card = scenario_loader.get_scenario(scenarios(), "call_09")
        kw = rb.session_kwargs_for_scenario(card, self._Cfg())
        assert kw["silence_ms"] == 600
        assert kw["allow_barge_in"] is False
        assert kw["voice"] in rb.VOICE_POOL

    def test_scenario_overrides_respected(self):
        card = {"call_id": "call_x", "vad_silence_ms": 450, "allow_barge_in": True, "realtime_voice": "verse"}
        kw = rb.session_kwargs_for_scenario(card, self._Cfg())
        assert kw["silence_ms"] == 450
        assert kw["allow_barge_in"] is True
        assert kw["voice"] == "verse"

    def test_kwargs_feed_build_session_update(self):
        card = scenario_loader.get_scenario(scenarios(), "call_03")
        kw = rb.session_kwargs_for_scenario(card, self._Cfg())
        sess = rb.build_session_update("INSTR", **kw)["session"]
        assert sess["audio"]["output"]["voice"] == kw["voice"]
        assert sess["audio"]["input"]["turn_detection"]["silence_duration_ms"] == 600
