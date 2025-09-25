#!/usr/bin/env python3
"""Ensure Vercel project metadata uses repository root as project root."""

from __future__ import annotations

import json
from pathlib import Path
import sys


def main() -> None:
    project_file = Path("frontend/.vercel/project.json")

    if not project_file.exists():
        sys.exit("project.json not found after vercel pull")

    data = json.loads(project_file.read_text())
    settings = data.get("projectSettings") or {}

    desired_root = "frontend"
    root = settings.get("rootDirectory")
    if root == desired_root:
        return

    settings["rootDirectory"] = desired_root
    data["projectSettings"] = settings
    project_file.write_text(json.dumps(data, indent=2) + "\n")


if __name__ == "__main__":
    main()
