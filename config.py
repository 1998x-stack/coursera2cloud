"""Configuration loading and path resolution."""

import os
from pathlib import Path

import yaml

from constants import PROJECT_ROOT


def _nested_get(d: dict, dotted_key: str):
    """Resolve 'section.subsection.key' against a nested dict."""
    node = d
    for part in dotted_key.split("."):
        if not isinstance(node, dict):
            raise KeyError(dotted_key)
        node = node[part]
    return node


def load_config(config_path: Path) -> dict:
    raw = yaml.safe_load(config_path.read_text())
    if raw is None:
        raw = {}
    env_keys = [
        ("auth", "coursera_cauth"),
        ("auth", "baidu_bduss"),
        ("auth", "baidu_stoken"),
    ]
    for section, key in env_keys:
        try:
            raw[section][key] = os.path.expandvars(raw[section][key])
        except KeyError:
            pass
    try:
        raw["download"]["tmp_dir"] = os.path.expandvars(raw["download"]["tmp_dir"])
    except KeyError:
        pass
    return raw


def resolve_path(config: dict, dotted_key: str) -> Path:
    p = Path(_nested_get(config, dotted_key))
    return p if p.is_absolute() else PROJECT_ROOT / p
