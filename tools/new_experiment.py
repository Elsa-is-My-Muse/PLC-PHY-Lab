"""Create a numbered experiment from the template without marking it completed."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path


def create_experiment(root: Path, slug: str, title: str) -> Path:
    if not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", slug) or len(slug) > 64:
        raise ValueError("slug must use lowercase ASCII letters, digits and single hyphens; max 64 characters")
    if not title.strip() or "\n" in title or "\r" in title:
        raise ValueError("title must be one nonempty line")
    index_path = root / "experiments/index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    if index.get("schema") != "plc-phy-lab.experiments.v1":
        raise ValueError("Unsupported experiment index schema")
    entries = index["experiments"]
    if any(entry["slug"] == slug for entry in entries):
        raise ValueError("An experiment with this slug already exists")
    number = max((int(entry["id"].removeprefix("EXP-")) for entry in entries), default=0) + 1
    identifier = f"EXP-{number:04d}"
    directory = root / "experiments" / f"{identifier}-{slug}"
    content = (root / "templates/experiment.md").read_text(encoding="utf-8")
    today = date.today().isoformat()
    for key, value in {"id": identifier, "title": title.strip(), "date": today}.items():
        content = content.replace("{{" + key + "}}", value)
    directory.mkdir(exist_ok=False)
    (directory / "README.md").write_text(content, encoding="utf-8", newline="\n")
    entries.append({"id": identifier, "slug": slug, "title": title.strip(), "status": "planned",
                    "recorded_date": today, "performed_date": None,
                    "path": f"{directory.name}/README.md"})
    temporary = index_path.with_name("index.json.tmp")
    with temporary.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(index, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    os.replace(temporary, index_path)
    return directory


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        directory = create_experiment(args.root, args.slug, args.title)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"Experiment error: {error}", file=sys.stderr)
        return 2
    print(f"Planned experiment created: {directory}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
