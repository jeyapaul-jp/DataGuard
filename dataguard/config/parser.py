from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .models import DataguardConfig

ENV_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")


class ConfigError(Exception):
    pass


def _resolve_env_vars(value: Any, missing: list[str]) -> Any:
    """Recursively substitute ${VAR} references in strings; track missing vars."""
    if isinstance(value, str):
        def replacer(m: re.Match) -> str:
            var = m.group(1)
            resolved = os.environ.get(var)
            if resolved is None:
                missing.append(var)
                return f"__MISSING_ENV:{var}__"
            return resolved
        return ENV_VAR_PATTERN.sub(replacer, value)
    if isinstance(value, dict):
        return {k: _resolve_env_vars(v, missing) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env_vars(item, missing) for item in value]
    return value


def parse_config(path: str) -> tuple[DataguardConfig, dict[str, list[str]]]:
    """Load, resolve env vars, and validate a DataGuard config file.

    Returns (config, missing_env_vars) where missing_env_vars maps
    connection name → list of missing environment variable names.
    Raises ConfigError on syntax or validation failure.
    """
    path_obj = Path(path)
    if not path_obj.exists():
        raise ConfigError(f"Config file not found: {path}")

    raw_text = path_obj.read_text(encoding="utf-8")

    try:
        if path_obj.suffix in (".yaml", ".yml"):
            raw: Any = yaml.safe_load(raw_text)
        elif path_obj.suffix == ".json":
            raw = json.loads(raw_text)
        else:
            try:
                raw = yaml.safe_load(raw_text)
            except yaml.YAMLError:
                raw = json.loads(raw_text)
    except (yaml.YAMLError, json.JSONDecodeError) as exc:
        raise ConfigError(f"Parse error in {path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigError(f"Config file {path} must be a YAML/JSON object, got {type(raw).__name__}")

    # Resolve env vars per connection; track missing vars by connection name
    missing_env_vars: dict[str, list[str]] = {}
    connections_raw = raw.get("connections", {}) or {}
    resolved_connections: dict[str, Any] = {}
    for conn_name, conn_data in connections_raw.items():
        missing: list[str] = []
        resolved_connections[conn_name] = _resolve_env_vars(conn_data, missing)
        if missing:
            missing_env_vars[conn_name] = missing
    raw["connections"] = resolved_connections

    try:
        config = DataguardConfig.model_validate(raw)
    except ValidationError as exc:
        raise ConfigError(f"Validation error in {path}:\n{exc}") from exc

    return config, missing_env_vars
