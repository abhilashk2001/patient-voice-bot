"""Tests for src/telephony.py — TwiML, Twilio media framing, dial guard (Phase 04)."""
import json
from types import SimpleNamespace

import pytest

import telephony
from config import UnauthorizedTargetError


class TestStreamTwiml:
    def test_contains_connect_and_stream_url(self):
        xml = telephony.build_stream_twiml("wss://abc.ngrok-free.app/media")
        assert "<Response>" in xml
        assert "<Connect>" in xml
        assert "wss://abc.ngrok-free.app/media" in xml

    def test_is_wellformed_xml(self):
        import xml.dom.minidom as minidom

        xml = telephony.build_stream_twiml("wss://x/media")
        minidom.parseString(xml)  # raises if malformed


class TestMediaMessage:
    def test_build_media_message_roundtrips(self):
        msg = telephony.build_media_message("MZ123", "QUJD")
        parsed = json.loads(msg)
        assert parsed["event"] == "media"
        assert parsed["streamSid"] == "MZ123"
        assert parsed["media"]["payload"] == "QUJD"


class TestParseTwilioMessage:
    def test_parse_start(self):
        raw = json.dumps(
            {"event": "start", "streamSid": "MZ1", "start": {"streamSid": "MZ1", "callSid": "CA1"}}
        )
        m = telephony.parse_twilio_message(raw)
        assert m["event"] == "start"
        assert m["stream_sid"] == "MZ1"

    def test_parse_media_extracts_payload(self):
        raw = json.dumps({"event": "media", "streamSid": "MZ1", "media": {"payload": "QUJD"}})
        m = telephony.parse_twilio_message(raw)
        assert m["event"] == "media"
        assert m["payload"] == "QUJD"

    def test_parse_stop(self):
        m = telephony.parse_twilio_message(json.dumps({"event": "stop", "streamSid": "MZ1"}))
        assert m["event"] == "stop"

    def test_media_without_payload_is_none(self):
        m = telephony.parse_twilio_message(json.dumps({"event": "connected"}))
        assert m["event"] == "connected"
        assert m["payload"] is None


class FakeCalls:
    def __init__(self):
        self.created = None

    def create(self, **kwargs):
        self.created = kwargs
        return SimpleNamespace(sid="CA_TEST")


class FakeClient:
    def __init__(self):
        self.calls = FakeCalls()


class TestPlaceOutboundCall:
    def test_authorized_number_places_call(self):
        client = FakeClient()
        sid = telephony.place_outbound_call(
            client, to="+1-805-439-8008", from_="+13334445555", twiml="<Response/>"
        )
        assert sid == "CA_TEST"
        # normalized target passed through
        assert client.calls.created["to"] == "+18054398008"
        assert client.calls.created["from_"] == "+13334445555"

    def test_unauthorized_number_refused_before_dialing(self):
        client = FakeClient()
        with pytest.raises(UnauthorizedTargetError):
            telephony.place_outbound_call(
                client, to="+19998887777", from_="+13334445555", twiml="<Response/>"
            )
        # never touched the client
        assert client.calls.created is None
