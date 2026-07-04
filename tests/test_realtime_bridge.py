"""Tests for src/realtime_bridge.py — GA Realtime session + event translation (Phase 04).

Reflects the GA `gpt-realtime` API shape: session.type="realtime", nested
audio.input/audio.output, output_modalities, and audio/pcmu (G.711 u-law) so
Twilio's 8 kHz mu-law passes through without resampling.
"""
import json

import realtime_bridge as rb


class TestSessionUpdate:
    def test_top_level_shape(self):
        s = rb.build_session_update("BE A PATIENT")
        assert s["type"] == "session.update"
        assert s["session"]["type"] == "realtime"
        assert s["session"]["instructions"] == "BE A PATIENT"
        assert s["session"]["output_modalities"] == ["audio"]

    def test_pcmu_passthrough_both_directions(self):
        sess = rb.build_session_update("x")["session"]
        assert sess["audio"]["input"]["format"]["type"] == "audio/pcmu"
        assert sess["audio"]["output"]["format"]["type"] == "audio/pcmu"

    def test_server_vad_with_silence(self):
        td = rb.build_session_update("x", silence_ms=600)["session"]["audio"]["input"]["turn_detection"]
        assert td["type"] == "server_vad"
        assert td["silence_duration_ms"] == 600

    def test_end_call_tool_present(self):
        tools = rb.build_session_update("x")["session"]["tools"]
        assert "end_call" in [t.get("name") for t in tools]

    def test_custom_voice(self):
        sess = rb.build_session_update("x", voice="verse")["session"]
        assert sess["audio"]["output"]["voice"] == "verse"

    def test_enables_input_transcription_for_transcripts(self):
        sess = rb.build_session_update("x")["session"]
        assert sess["audio"]["input"].get("transcription") is not None


class TestAudioAppend:
    def test_wraps_payload(self):
        m = rb.build_audio_append("QUJD")
        assert m["type"] == "input_audio_buffer.append"
        assert m["audio"] == "QUJD"


class TestExtractAudioDelta:
    def test_returns_delta_for_ga_audio_event(self):
        assert rb.extract_audio_delta({"type": "response.output_audio.delta", "delta": "QUJD"}) == "QUJD"

    def test_returns_delta_for_legacy_audio_event(self):
        assert rb.extract_audio_delta({"type": "response.audio.delta", "delta": "QUJD"}) == "QUJD"

    def test_none_for_other_events(self):
        assert rb.extract_audio_delta({"type": "response.text.delta", "delta": "hi"}) is None
        assert rb.extract_audio_delta({"type": "session.updated"}) is None


class TestExtractEndCallReason:
    def test_reads_reason_from_arguments_done(self):
        ev = {
            "type": "response.function_call_arguments.done",
            "name": "end_call",
            "arguments": json.dumps({"reason": "appointment confirmed"}),
        }
        assert rb.extract_end_call_reason(ev) == "appointment confirmed"

    def test_reads_reason_from_output_item_done(self):
        ev = {
            "type": "response.output_item.done",
            "item": {"type": "function_call", "name": "end_call", "arguments": json.dumps({"reason": "done"})},
        }
        assert rb.extract_end_call_reason(ev) == "done"

    def test_none_for_other_function(self):
        ev = {"type": "response.function_call_arguments.done", "name": "other", "arguments": "{}"}
        assert rb.extract_end_call_reason(ev) is None

    def test_none_for_non_function_event(self):
        assert rb.extract_end_call_reason({"type": "response.output_audio.delta"}) is None

    def test_handles_missing_reason_gracefully(self):
        ev = {"type": "response.function_call_arguments.done", "name": "end_call", "arguments": "{}"}
        assert rb.extract_end_call_reason(ev) == ""
