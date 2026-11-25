"""Check local documentation links, JSON records, and GNU Radio source settings."""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import unquote

import yaml

ROOT = Path(__file__).resolve().parents[1]
STATUSES = {"reported_prior_session", "planned", "in_progress", "completed", "inconclusive"}


def main() -> int:
    errors = []
    documents = [path for path in ROOT.rglob("*.md") if not any(part in {".git", ".venv", "build", "__pycache__"} for part in path.parts)]
    for path in documents:
        text = path.read_text(encoding="utf-8")
        if "\ufffd" in text:
            errors.append(f"Replacement character in {path.relative_to(ROOT)}")
        for target in re.findall(r"!?\[[^\]]*\]\(([^)\s]+)\)", text):
            if target.startswith(("https://", "http://", "#", "mailto:")):
                continue
            relative = unquote(target.split("#", 1)[0])
            if relative and not (path.parent / relative).exists():
                errors.append(f"Broken local link in {path.relative_to(ROOT)}: {target}")
    for path in (ROOT / "hardware/inventory.json", ROOT / "experiments/index.json"):
        json.loads(path.read_text(encoding="utf-8"))
    entries = json.loads((ROOT / "experiments/index.json").read_text(encoding="utf-8"))["experiments"]
    ids = [entry["id"] for entry in entries]
    if len(ids) != len(set(ids)):
        errors.append("Duplicate experiment IDs")
    for entry in entries:
        if entry["status"] not in STATUSES:
            errors.append(f"Unknown experiment status: {entry['id']}")
        if not (ROOT / "experiments" / entry["path"]).is_file():
            errors.append(f"Missing experiment record: {entry['id']}")
    for path in (ROOT / "sdr/gnuradio").glob("*.grc"):
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        source = next(block for block in document["blocks"] if block["id"] == "soapy_hackrf_source")
        if float(source["parameters"]["bandwidth"]) != 20e6 or source["parameters"]["amp"] != "False":
            errors.append(f"Unexpected default RF source settings: {path.name}")
        if "C:/Users/" in path.read_text(encoding="utf-8"):
            errors.append(f"Machine-specific capture path: {path.name}")
    for path in (ROOT / ".github").rglob("*.yml"):
        yaml.safe_load(path.read_text(encoding="utf-8"))
    if errors:
        print("\n".join(errors))
        return 1
    print(f"Project checks passed: {len(documents)} Markdown documents; {len(entries)} experiment records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
