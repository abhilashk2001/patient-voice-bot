"""Configuration loading and the authorized-number guard (Phase 01, FR1).

The single most important rule in this project: the app must refuse to place a
call to any number except the authorized assessment line. That check lives here
and runs before any telephony provider is ever contacted.
"""
import os
from dataclasses import dataclass
from typing import Mapping, Optional

from utils import normalize_phone

# The only number this bot is ever allowed to call (challenge requirement).
AUTHORIZED_TARGET = "+18054398008"

# Keys that must be present for a real run.
_REQUIRED_KEYS = (
    "TARGET_PHONE_NUMBER",
    "CALLER_PHONE_NUMBER",
    "OPENAI_API_KEY",
)


class ConfigError(Exception):
    """Base class for configuration problems."""


class MissingConfigError(ConfigError):
    """A required setting is absent or empty."""


class UnauthorizedTargetError(ConfigError):
    """The configured target number is not the authorized assessment line."""


def validate_target_number(raw: Optional[str]) -> str:
    """Normalize and authorize a target phone number.

    Returns the normalized number if it is the authorized target; otherwise
    raises. An empty/None value is treated as missing configuration.
    """
    if raw is None or raw.strip() == "":
        raise MissingConfigError("TARGET_PHONE_NUMBER is not set")
    normalized = normalize_phone(raw)
    if normalized != AUTHORIZED_TARGET:
        raise UnauthorizedTargetError(
            f"Refusing to call {normalized!r}; only {AUTHORIZED_TARGET} is authorized."
        )
    return normalized


def _bool(value: Optional[str]) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Config:
    target_phone_number: str
    caller_phone_number: str
    openai_api_key: str
    openai_realtime_model: str
    call_output_dir: str
    scenarios_file: str
    max_call_seconds: int
    recent_turns_limit: int
    dry_run: bool
    # Telephony / bridge settings — optional at load time (only needed for real
    # calls). call_runner.validate_ready_for_call enforces them before dialing.
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    public_media_stream_url: str = ""
    realtime_voice: str = "alloy"
    media_server_port: int = 8080


def load_config(env: Optional[Mapping[str, str]] = None) -> Config:
    """Build a validated :class:`Config` from an environment mapping.

    Defaults to ``os.environ`` but accepts any mapping (used in tests). The
    authorized-number guard runs first, before anything else is assembled.
    """
    if env is None:
        env = os.environ

    # Guard first — refuse unauthorized targets before doing any other work.
    target = validate_target_number(env.get("TARGET_PHONE_NUMBER"))

    for key in _REQUIRED_KEYS:
        if not (env.get(key) or "").strip():
            raise MissingConfigError(f"Required setting {key} is not set")

    return Config(
        target_phone_number=target,
        caller_phone_number=normalize_phone(env.get("CALLER_PHONE_NUMBER", "")),
        openai_api_key=env["OPENAI_API_KEY"],
        openai_realtime_model=env.get("OPENAI_REALTIME_MODEL", "gpt-realtime"),
        call_output_dir=env.get("CALL_OUTPUT_DIR", "./calls"),
        scenarios_file=env.get("SCENARIOS_FILE", "./scenarios/scenarios.json"),
        max_call_seconds=int(env.get("MAX_CALL_SECONDS", "180")),
        recent_turns_limit=int(env.get("RECENT_TURNS_LIMIT", "6")),
        dry_run=_bool(env.get("DRY_RUN", "false")),
        twilio_account_sid=env.get("TWILIO_ACCOUNT_SID", ""),
        twilio_auth_token=env.get("TWILIO_AUTH_TOKEN", ""),
        twilio_phone_number=normalize_phone(env.get("TWILIO_PHONE_NUMBER", "")),
        public_media_stream_url=env.get("PUBLIC_MEDIA_STREAM_URL", ""),
        realtime_voice=env.get("REALTIME_VOICE", "alloy"),
        media_server_port=int(env.get("MEDIA_SERVER_PORT", "8080")),
    )
