#!/usr/bin/env python3
"""Export skill-issue stats as JSON or CSV for external analysis."""

import csv
import json
import sys
from pathlib import Path

SKILL_DIR = Path.home() / ".skill-issue"


def export_json(output_path: str = None):
    with open(SKILL_DIR / "profile.json") as f:
        profile = json.load(f)

    sessions = []
    for sf in sorted((SKILL_DIR / "sessions").glob("*.json")):
        with open(sf) as f:
            sessions.append(json.load(f))

    export = {"profile": profile, "sessions": sessions}

    if output_path:
        with open(output_path, "w") as f:
            json.dump(export, f, indent=2)
        print(f"Exported to {output_path}")
    else:
        print(json.dumps(export, indent=2))


def export_csv(output_path: str = None):
    rows = []
    for sf in sorted((SKILL_DIR / "sessions").glob("*.json")):
        with open(sf) as f:
            session = json.load(f)
        for c in session.get("challenges", []):
            rows.append({
                "session": session["session_id"],
                "challenge_id": c["id"],
                "timestamp": c["timestamp"],
                "type": c["type"],
                "topic": c["topic"],
                "difficulty": c["difficulty"],
                "score": c["score"],
                "xp_earned": c["xp_earned"],
                "hint_used": c["hint_used"],
            })

    if not rows:
        print("No challenge data to export.")
        return

    out = sys.stdout
    if output_path:
        out = open(output_path, "w", newline="")

    writer = csv.DictWriter(out, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

    if output_path:
        out.close()
        print(f"Exported {len(rows)} challenges to {output_path}")


if __name__ == "__main__":
    fmt = sys.argv[1] if len(sys.argv) > 1 else "json"
    path = sys.argv[2] if len(sys.argv) > 2 else None
    if fmt == "csv":
        export_csv(path)
    else:
        export_json(path)
