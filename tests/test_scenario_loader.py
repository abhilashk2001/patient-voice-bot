"""Tests for src/scenario_loader.py and the real scenarios.json (Phase 02, FR2)."""
import pytest

import scenario_loader

REQUIRED_KEYS = {
    "call_id",
    "scenario_name",
    "persona",
    "tone",
    "patient_goal",
    "medical_or_clinic_issue",
    "hidden_details",
    "speaking_style",
    "edge_case",
    "stop_condition",
    "expected_assistant_behavior",
    "bug_indicators",
}

SCENARIOS_PATH = "scenarios/scenarios.json"


@pytest.fixture
def scenarios():
    return scenario_loader.load_scenarios(SCENARIOS_PATH)


class TestRealScenarioFile:
    def test_has_exactly_ten(self, scenarios):
        assert len(scenarios) == 10

    def test_call_ids_are_call_01_through_10(self, scenarios):
        ids = [s["call_id"] for s in scenarios]
        assert ids == [f"call_{i:02d}" for i in range(1, 11)]

    def test_every_card_has_required_keys(self, scenarios):
        for s in scenarios:
            assert REQUIRED_KEYS <= set(s), f"{s.get('call_id')} missing keys"

    def test_edge_case_shape(self, scenarios):
        for s in scenarios:
            ec = s["edge_case"]
            assert {"type", "enabled", "rules"} <= set(ec)
            assert isinstance(ec["enabled"], bool)
            assert isinstance(ec["rules"], list)

    def test_call_02_has_edge_case_disabled(self, scenarios):
        card = scenario_loader.get_scenario(scenarios, "call_02")
        assert card["edge_case"]["enabled"] is False

    def test_call_09_is_math_drift(self, scenarios):
        card = scenario_loader.get_scenario(scenarios, "call_09")
        assert card["edge_case"]["type"] == "gradual_off_topic_math"
        assert any("pi" in r.lower() for r in card["edge_case"]["rules"])


class TestGetScenario:
    def test_returns_matching_card(self, scenarios):
        card = scenario_loader.get_scenario(scenarios, "call_05")
        assert card["scenario_name"] == "Cancel appointment"

    def test_unknown_id_raises(self, scenarios):
        with pytest.raises(KeyError):
            scenario_loader.get_scenario(scenarios, "call_99")


class TestListScenarios:
    def test_returns_id_name_pairs(self, scenarios):
        listing = scenario_loader.list_scenarios(scenarios)
        assert len(listing) == 10
        assert ("call_01", "Clinic hours and location baseline") in listing


class TestValidateScenario:
    def test_valid_card_passes(self, scenarios):
        scenario_loader.validate_scenario(scenarios[0])  # no raise

    def test_missing_key_raises(self):
        bad = {"call_id": "call_x"}
        with pytest.raises(scenario_loader.ScenarioError):
            scenario_loader.validate_scenario(bad)
