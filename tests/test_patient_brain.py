"""Tests for src/patient_brain.py — scenario -> Realtime instructions (Phase 02)."""
import pytest

import patient_brain
import scenario_loader

CALLER = "+13334445555"
NAME = "Abhilash Kaluwala"
DOB = "13 February 2001"


@pytest.fixture
def scenarios():
    return scenario_loader.load_scenarios("scenarios/scenarios.json")


def instructions_for(scenarios, call_id):
    card = scenario_loader.get_scenario(scenarios, call_id)
    return patient_brain.build_instructions(
        card, caller_number=CALLER, patient_name=NAME, patient_dob=DOB
    )


class TestCommonStructure:
    def test_returns_nonempty_string(self, scenarios):
        text = instructions_for(scenarios, "call_02")
        assert isinstance(text, str) and text.strip()

    def test_includes_base_identity(self, scenarios):
        text = instructions_for(scenarios, "call_02")
        assert "Pivot Point Orthopaedics" in text

    def test_includes_persona_and_goal(self, scenarios):
        text = instructions_for(scenarios, "call_02")
        card = scenario_loader.get_scenario(scenarios, "call_02")
        assert card["persona"] in text
        assert card["patient_goal"] in text

    def test_includes_stop_condition(self, scenarios):
        text = instructions_for(scenarios, "call_02")
        card = scenario_loader.get_scenario(scenarios, "call_02")
        assert card["stop_condition"] in text


class TestFixedIdentity:
    def test_injects_name_and_dob(self, scenarios):
        text = instructions_for(scenarios, "call_02")
        assert NAME in text
        assert DOB in text

    def test_instructs_not_to_invent_identity(self, scenarios):
        text = instructions_for(scenarios, "call_02").lower()
        assert "do not invent" in text or "never invent" in text
        assert "verify" in text or "verification" in text

    def test_identity_absent_when_not_provided(self, scenarios):
        # Backwards-compatible: no identity args -> no identity block, no crash.
        card = scenario_loader.get_scenario(scenarios, "call_02")
        text = patient_brain.build_instructions(card, caller_number=CALLER)
        assert NAME not in text

    def test_instructs_end_call_with_goodbye(self, scenarios):
        text = instructions_for(scenarios, "call_02").lower()
        assert "end_call" in text
        assert "goodbye" in text or "bye" in text


class TestCallerNumberSubstitution:
    def test_placeholder_replaced_with_caller_number(self, scenarios):
        text = instructions_for(scenarios, "call_02")
        assert CALLER in text
        assert "use configured caller number" not in text


class TestOnFilePhone:
    def test_on_file_phone_takes_precedence(self, scenarios):
        # When a registered on-file number is given, the patient states THAT,
        # not the Twilio caller number, so verification matches the account.
        on_file = "+15550001234"
        card = scenario_loader.get_scenario(scenarios, "call_02")
        text = patient_brain.build_instructions(
            card, caller_number=CALLER, patient_name=NAME, patient_dob=DOB, patient_phone=on_file
        )
        assert on_file in text
        assert CALLER not in text

    def test_falls_back_to_caller_when_no_on_file(self, scenarios):
        card = scenario_loader.get_scenario(scenarios, "call_02")
        text = patient_brain.build_instructions(
            card, caller_number=CALLER, patient_name=NAME, patient_dob=DOB
        )
        assert CALLER in text


class TestEdgeCaseStaging:
    def test_enabled_edge_case_renders_staged_rules(self, scenarios):
        text = instructions_for(scenarios, "call_09")
        assert "8 plus 9" in text
        assert "pi" in text.lower()
        # each rule should surface in the staged section
        card = scenario_loader.get_scenario(scenarios, "call_09")
        for rule in card["edge_case"]["rules"]:
            assert rule in text

    def test_enabled_marks_gradual_introduction(self, scenarios):
        text = instructions_for(scenarios, "call_09").lower()
        assert "gradual" in text or "only when" in text or "only if" in text

    def test_disabled_edge_case_has_no_probe_section(self, scenarios):
        text = instructions_for(scenarios, "call_02")
        # call_02 has edge_case.enabled == False -> no staged probe rules
        assert "straightforward" in text.lower()
