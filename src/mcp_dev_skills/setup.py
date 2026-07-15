"""Interactive CLI for setting up .skills.json configuration."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .loader import build_skill_tree


class SkillTreeSelector:
    """Interactive terminal UI for selecting skills."""

    def __init__(self):
        self.selected_paths: set[str] = set()

    def _flatten_tree(self, node: dict, parent_path: str = "") -> list[tuple[str, dict]]:
        """Flatten skill tree into (path, node) tuples."""
        items = []
        current_path = f"{parent_path}.{node['name']}" if parent_path else node["name"]

        if node.get("type") == "dir":
            for child in node.get("children", []):
                items.extend(self._flatten_tree(child, current_path))
        else:
            items.append((current_path, node))

        return items

    def run(self, workspace_root: Path) -> None:
        """Run interactive selection."""
        tree = build_skill_tree()
        skills = self._flatten_tree(tree)

        if not skills:
            print("❌ No skills found.")
            return

        print("\n" + "=" * 60)
        print("  📦 Skills Installer")
        print("=" * 60)
        print()
        print("Select skill groups to enable (space to toggle, Enter to confirm):")
        print()

        # Simple menu: show all paths with numbers
        for i, (path, node) in enumerate(skills, 1):
            desc = node.get("description", "")[:40]
            print(f"  [{i:2}] {path:<30} {desc}")

        print()
        print("Enter selection (comma-separated numbers, or 'all', or 'none'):")
        user_input = input("> ").strip().lower()

        if user_input == "all":
            self.selected_paths = {path for path, _ in skills}
        elif user_input == "none":
            self.selected_paths = set()
        else:
            try:
                indices = [int(x.strip()) - 1 for x in user_input.split(",") if x.strip()]
                for idx in indices:
                    if 0 <= idx < len(skills):
                        self.selected_paths.add(skills[idx][0])
            except ValueError:
                print("❌ Invalid input.")
                return

        # Write config
        if self.selected_paths:
            self._write_config(workspace_root)
        else:
            print("⚠️  No skills selected. .skills.json not created.")

    def _write_config(self, workspace_root: Path) -> None:
        """Write .skills.json file."""
        config = {
            "enabled_paths": sorted(self.selected_paths),
            "disabled_skills": [],
        }
        config_path = workspace_root / ".skills.json"
        config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False))
        print()
        print("✓ Created .skills.json with the following enabled paths:")
        for path in sorted(self.selected_paths):
            print(f"  - {path}")
        print()


def run_setup() -> None:
    """Entry point for setup CLI."""
    workspace_root = Path.cwd()

    try:
        selector = SkillTreeSelector()
        selector.run(workspace_root)
    except KeyboardInterrupt:
        print("\n⚠️  Setup cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
