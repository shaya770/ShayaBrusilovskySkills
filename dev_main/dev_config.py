"""Master configuration and orchestrator for ShayaBrusilovskySkills.

Central point for configuring which skills to use for different operations:
- Testing: which skill runs tests?
- Deployment: which skill deploys?
- Build: how to build the project?
- Versioning: how to version?
- Logging: how to log decisions?

This is NOT a skill, but a configuration layer that tells skills HOW to work.
"""

from __future__ import annotations

import json
from pathlib import Path

# Default configuration for ShayaBrusilovskySkills
DEFAULT_CONFIG = {
    "project": "ShayaBrusilovskySkills",
    "development_strategy": "methodology_three_stage",
    "branching_mode": "simple",
    "local_dev_strategy": "local_dev_default",
    "autonomous_mode": True,

    # Operations: which skill/script to use
    "operations": {
        "test": {
            "command": "pytest",
            "directory": "tests/",
            "on_failure": "rollback_and_retry",
        },
        "deploy": {
            "command": "docker push && kubectl apply",
            "on_failure": "rollback_to_previous",
        },
        "build": {
            "command": "python -m build",
            "on_failure": "retry_with_clean",
        },
        "versioning": {
            "scheme": "semver",
            "format": "v{major}.{minor}.{patch}",
        },
        "logging": {
            "decisions": True,
            "file": ".dev_decisions.log",
        },
    },

    # Skills configuration
    "skills": {
        "enabled_paths": [
            "development.common",
            "development.trello",
            "development.branching",
            "development.local_dev",
            "development.development_rules:methodology_three_stage",
            "development.server_development",
        ],
    },
}


def load_config(config_file: Path | None = None) -> dict:
    """Load master configuration."""
    if config_file is None:
        config_file = Path(__file__).parent / "dev_config.json"

    if config_file.exists():
        try:
            return json.loads(config_file.read_text())
        except (json.JSONDecodeError, IOError):
            return DEFAULT_CONFIG

    return DEFAULT_CONFIG


def save_config(config: dict, config_file: Path | None = None) -> None:
    """Save master configuration."""
    if config_file is None:
        config_file = Path(__file__).parent / "dev_config.json"

    config_file.write_text(json.dumps(config, indent=2))


def get_operation(operation_name: str, config: dict | None = None) -> dict | None:
    """Get operation configuration."""
    if config is None:
        config = load_config()

    return config.get("operations", {}).get(operation_name)


def show_config(config: dict | None = None) -> str:
    """Return human-readable configuration."""
    if config is None:
        config = load_config()

    output = f"""# Master Configuration for {config.get('project', 'Unknown')}

## Development Strategy
- Strategy: {config.get('development_strategy', 'unknown')}
- Branching: {config.get('branching_mode', 'unknown')}
- Local Dev: {config.get('local_dev_strategy', 'unknown')}
- Autonomous Mode: {'Enabled' if config.get('autonomous_mode') else 'Disabled'}

## Operations
"""

    for op_name, op_config in config.get("operations", {}).items():
        output += f"\n### {op_name.title()}\n"
        for key, value in op_config.items():
            output += f"  - {key}: {value}\n"

    output += f"""
## Enabled Skills
"""
    for path in config.get("skills", {}).get("enabled_paths", []):
        output += f"  - {path}\n"

    return output


# Example usage and testing
if __name__ == "__main__":
    config = load_config()
    print(show_config(config))
    print("\n" + "="*60)
    print("\nExample: Get test operation config")
    test_op = get_operation("test", config)
    print(json.dumps(test_op, indent=2))
