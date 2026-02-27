#!/usr/bin/env python3
"""Initialize the ~/.skill-issue/ directory with default files."""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

SKILL_DIR = Path.home() / ".skill-issue"

DEFAULT_CONFIG = """# skill-issue configuration
frequency:
  cooldown_minutes: 8
  challenge_probability: 0.6
  max_per_session: 20

difficulty:
  bias: 0
  auto_adapt: true

challenge_types:
  pen-paper: true
  explain-back: true
  predict: true
  spot-bug: true
  complexity: true
  connect-dots: true

display:
  show_xp_after_challenge: true
  show_streak: true
  celebration_messages: true
  compact_mode: false

domains: []

focus_mode: false
quiet_hours: []
"""


def init_profile(username: str = None, domains: list = None, force: bool = False):
    if SKILL_DIR.exists():
        if not force:
            print(f"skill-issue directory already exists at {SKILL_DIR}")
            return
        import shutil
        shutil.rmtree(SKILL_DIR)
        print(f"Reinitializing {SKILL_DIR}...")

    SKILL_DIR.mkdir(parents=True)
    (SKILL_DIR / "sessions").mkdir()

    profile = {
        "version": 2,
        "username": username or os.environ.get("USER", "human"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "overall_level": "Apprentice",
        "total_xp": 0,
        "total_challenges": 0,
        "scores": {"0": 0, "1": 0, "2": 0, "3": 0},
        "current_streak": 0,
        "best_streak": 0,
        "topics": {},
        "preferences": {
            "challenge_frequency": "normal",
            "difficulty_bias": 0,
            "focus_mode": False,
            "enabled_types": [
                "pen-paper", "explain-back", "predict",
                "spot-bug", "complexity", "connect-dots"
            ]
        },
        "milestones": [],
        "next_challenge_id": 1
    }

    with open(SKILL_DIR / "profile.json", "w") as f:
        json.dump(profile, f, indent=2)

    config_text = DEFAULT_CONFIG
    if domains:
        domain_lines = "\n".join(f"  - {d}" for d in domains)
        config_text = config_text.replace("domains: []", f"domains:\n{domain_lines}")
    with open(SKILL_DIR / "config.yaml", "w") as f:
        f.write(config_text)

    with open(SKILL_DIR / "leaderboard.md", "w") as f:
        name = profile["username"]
        f.write(f"# 🧠 skill-issue — Human Performance Dashboard\n\n")
        f.write(f"**Player**: {name}\n")
        f.write(f"**Level**: Apprentice (0 XP)\n\n")
        f.write(f"No challenges completed yet. Let's begin!\n")

    print(f"✓ Initialized skill-issue at {SKILL_DIR}")
    print(f"  Player: {profile['username']}")
    print(f"  Config: {SKILL_DIR / 'config.yaml'}")


if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else None
    init_profile(username)
