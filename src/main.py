"""Command-line entry point (Phase 03).

Commands (PRD §9.2):
    python src/main.py --list
    python src/main.py --scenario call_09 --dry-run
    python src/main.py --scenario call_09
    python src/main.py --all

`--dry-run` renders the Realtime instructions, runs the authorized-number guard,
and scaffolds the call output folder without placing a real call or spending
anything. Real calls arrive in Phase 04.
"""
import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Mapping, Optional

import config as config_mod
import patient_brain
import scenario_loader
from utils import ensure_dir, write_json


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="patient-voice-bot")
    p.add_argument("--list", action="store_true", help="List available scenarios")
    p.add_argument("--scenario", metavar="CALL_ID", help="Run a single scenario")
    p.add_argument("--all", action="store_true", help="Run all scenarios")
    p.add_argument("--dry-run", action="store_true", help="No real call; render + scaffold only")
    p.add_argument(
        "--fetch-recordings",
        action="store_true",
        help="Download any recordings still missing from saved call folders",
    )
    return p


def _scenarios_path(env: Mapping[str, str]) -> str:
    return env.get("SCENARIOS_FILE", "./scenarios/scenarios.json")


def _scaffold_call_folder(scenario: Dict, output_root: str) -> Path:
    """Create calls/<call_id>/ and drop the scenario snapshot in it (FR2)."""
    folder = ensure_dir(Path(output_root) / scenario["call_id"])
    write_json(folder / "scenario.json", scenario)
    return folder


def do_dry_run(scenario: Dict, cfg: config_mod.Config) -> None:
    print(f"[OK] scenario {scenario['call_id']} valid")
    print(f"[OK] target {cfg.target_phone_number} authorized")
    print("--- RENDERED REALTIME INSTRUCTIONS ---")
    print(
        patient_brain.build_instructions(
            scenario,
            caller_number=cfg.caller_phone_number,
            patient_name=cfg.patient_name,
            patient_dob=cfg.patient_dob,
            patient_phone=cfg.patient_phone_on_file,
        )
    )
    print("--- END ---")
    folder = _scaffold_call_folder(scenario, cfg.call_output_dir)
    print(f"[OK] scaffolded {folder}/")
    print("No call placed. No spend.")


def place_real_call(scenario: Dict, cfg: config_mod.Config) -> None:
    """Place a real call by bridging Twilio to OpenAI Realtime (Phase 04)."""
    import call_runner

    state = call_runner.place_call(scenario, cfg)
    print(f"[OK] call {state.get('call_sid')} finished: {state.get('outcome')}")


def _run_scenarios(call_ids: List[str], cfg: config_mod.Config, scenarios: List[Dict], dry_run: bool) -> int:
    for call_id in call_ids:
        try:
            card = scenario_loader.get_scenario(scenarios, call_id)
        except KeyError as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            return 1
        if dry_run:
            do_dry_run(card, cfg)
        else:
            try:
                place_real_call(card, cfg)
            except config_mod.ConfigError as e:
                print(f"[ERROR] {e}", file=sys.stderr)
                return 1
    return 0


def main(argv: Optional[List[str]] = None, env: Optional[Mapping[str, str]] = None) -> int:
    args = build_parser().parse_args(sys.argv[1:] if argv is None else argv)

    if env is None:
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except ImportError:
            pass
        env = os.environ

    # --list is cheap and must not depend on the auth guard.
    if args.list:
        scenarios = scenario_loader.load_scenarios(_scenarios_path(env))
        for call_id, name in scenario_loader.list_scenarios(scenarios):
            print(f"{call_id}  {name}")
        return 0

    if not args.scenario and not args.all and not args.fetch_recordings:
        print("[ERROR] Nothing to do. Use --list, --scenario <id>, --all, or --fetch-recordings.", file=sys.stderr)
        return 2

    # Any run path enforces the authorized-number guard first.
    try:
        cfg = config_mod.load_config(env)
    except config_mod.ConfigError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1

    if args.fetch_recordings:
        import recorder
        import telephony

        client = telephony.make_twilio_client(cfg.twilio_account_sid, cfg.twilio_auth_token)
        count = recorder.fetch_missing_recordings(
            cfg.call_output_dir, client,
            account_sid=cfg.twilio_account_sid, auth_token=cfg.twilio_auth_token,
        )
        print(f"[OK] fetched {count} missing recording(s)")
        return 0

    scenarios = scenario_loader.load_scenarios(cfg.scenarios_file)
    call_ids = [c["call_id"] for c in scenarios] if args.all else [args.scenario]
    return _run_scenarios(call_ids, cfg, scenarios, args.dry_run)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
