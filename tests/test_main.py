"""Tests for src/main.py — CLI + dry-run (Phase 03, FR2/FR3)."""
import main as main_mod
import utils


def make_env(tmp_path, **over):
    env = {
        "TARGET_PHONE_NUMBER": "+18054398008",
        "CALLER_PHONE_NUMBER": "+13334445555",
        "OPENAI_API_KEY": "sk-test",
        "OPENAI_REALTIME_MODEL": "gpt-realtime",
        "CALL_OUTPUT_DIR": str(tmp_path / "calls"),
        "SCENARIOS_FILE": "scenarios/scenarios.json",
        "MAX_CALL_SECONDS": "180",
        "RECENT_TURNS_LIMIT": "6",
        "DRY_RUN": "false",
    }
    env.update(over)
    return env


class TestList:
    def test_lists_all_ten(self, capsys, tmp_path):
        rc = main_mod.main(["--list"], env=make_env(tmp_path))
        out = capsys.readouterr().out
        assert rc == 0
        for i in range(1, 11):
            assert f"call_{i:02d}" in out
        assert "Clinic hours and location baseline" in out

    def test_list_does_not_require_valid_target(self, capsys, tmp_path):
        # listing is cheap and must not depend on the auth guard
        rc = main_mod.main(["--list"], env=make_env(tmp_path, TARGET_PHONE_NUMBER="+19999999999"))
        assert rc == 0


class TestDryRun:
    def test_scaffolds_folder_and_reports_no_spend(self, capsys, tmp_path):
        rc = main_mod.main(["--scenario", "call_09", "--dry-run"], env=make_env(tmp_path))
        out = capsys.readouterr().out
        assert rc == 0
        assert "authorized" in out
        assert "RENDERED REALTIME INSTRUCTIONS" in out
        assert "No call placed. No spend." in out
        folder = tmp_path / "calls" / "call_09"
        assert (folder / "scenario.json").is_file()
        assert utils.read_json(folder / "scenario.json")["call_id"] == "call_09"

    def test_renders_staged_prompt(self, capsys, tmp_path):
        main_mod.main(["--scenario", "call_09", "--dry-run"], env=make_env(tmp_path))
        assert "8 plus 9" in capsys.readouterr().out

    def test_unknown_scenario_errors(self, capsys, tmp_path):
        rc = main_mod.main(["--scenario", "call_99", "--dry-run"], env=make_env(tmp_path))
        cap = capsys.readouterr()
        assert rc != 0
        assert "call_99" in (cap.out + cap.err)


class TestGuard:
    def test_unauthorized_target_refused_on_dry_run(self, capsys, tmp_path):
        env = make_env(tmp_path, TARGET_PHONE_NUMBER="+13334445555")
        rc = main_mod.main(["--scenario", "call_02", "--dry-run"], env=env)
        cap = capsys.readouterr()
        assert rc != 0
        assert "Refusing to call" in (cap.out + cap.err)


class TestAll:
    def test_all_dry_run_scaffolds_ten(self, capsys, tmp_path):
        rc = main_mod.main(["--all", "--dry-run"], env=make_env(tmp_path))
        assert rc == 0
        for i in range(1, 11):
            assert (tmp_path / "calls" / f"call_{i:02d}" / "scenario.json").is_file()


class TestRealCallGuardrail:
    def test_real_call_requires_telephony_config(self, capsys, tmp_path):
        # Without --dry-run, a real call is attempted; the base env has no Twilio
        # creds, so the pre-flight check must refuse before dialing.
        rc = main_mod.main(["--scenario", "call_02"], env=make_env(tmp_path))
        cap = capsys.readouterr()
        assert rc != 0
        assert "telephony" in (cap.out + cap.err).lower()


class TestNoAction:
    def test_no_action_returns_error(self, capsys, tmp_path):
        rc = main_mod.main([], env=make_env(tmp_path))
        assert rc != 0
