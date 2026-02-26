#!/usr/bin/env python3
"""Update profile.json with a new challenge result."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SKILL_DIR = Path.home() / ".skill-issue"
PROFILE_PATH = SKILL_DIR / "profile.json"

XP_TABLE = {0: 0, 1: 5, 2: 12, 3: 20}
DIFF_MULT = {"Apprentice": 1.0, "Practitioner": 1.5, "Expert": 2.0, "Master": 3.0}
LEVEL_THRESHOLDS = [(5000, "Master"), (2000, "Expert"), (500, "Practitioner"), (0, "Apprentice")]


def calculate_xp(score: int, difficulty: str, streak: int, hint_used: bool) -> int:
    base = XP_TABLE[score]
    diff_m = DIFF_MULT[difficulty]
    streak_m = min(1.0 + streak * 0.15, 2.5)
    hint_p = 0.75 if hint_used else 1.0
    return round(base * diff_m * streak_m * hint_p)


def get_topic_level(topic_data: dict) -> str:
    scores = topic_data.get("scores", [])
    total = topic_data.get("attempts", 0)
    recent = scores[-20:] if len(scores) > 20 else scores
    if not recent:
        return "Apprentice"
    accuracy = sum(1 for s in recent if s >= 2) / len(recent)
    if accuracy >= 0.90 and total >= 15:
        return "Master"
    elif accuracy >= 0.75 and total >= 10:
        return "Expert"
    elif accuracy >= 0.55 and total >= 5:
        return "Practitioner"
    return "Apprentice"


def get_overall_level(xp: int) -> str:
    for threshold, level in LEVEL_THRESHOLDS:
        if xp >= threshold:
            return level
    return "Apprentice"


def check_milestones(profile: dict, score: int, topic: str) -> list:
    new = []
    now = datetime.now(timezone.utc).isoformat()
    existing = {m["type"] + m.get("topic", "") for m in profile["milestones"]}

    if profile["total_challenges"] == 1 and "first_challenge" not in existing:
        new.append({"type": "first_challenge", "date": now})

    streak = profile["current_streak"]
    for threshold in [5, 10, 20]:
        key = f"streak_{threshold}"
        if streak >= threshold and key not in existing:
            new.append({"type": key, "date": now})

    if topic in profile["topics"]:
        level = profile["topics"][topic]["level"]
        if level == "Expert" and f"topic_expert{topic}" not in existing:
            new.append({"type": "topic_expert", "topic": topic, "date": now})
        if level == "Master" and f"topic_master{topic}" not in existing:
            new.append({"type": "topic_master", "topic": topic, "date": now})

    for threshold in [500, 2000, 5000]:
        key = f"xp_{threshold}"
        if profile["total_xp"] >= threshold and key not in existing:
            new.append({"type": key, "date": now})

    # Check all_types milestone
    if "all_types" not in existing:
        used_types = set()
        for session_file in sorted((SKILL_DIR / "sessions").glob("*.json")):
            with open(session_file) as f:
                session = json.load(f)
            for c in session.get("challenges", []):
                used_types.add(c.get("type", ""))
        all_six = {"pen-paper", "explain-back", "predict", "spot-bug", "complexity", "connect-dots"}
        if all_six.issubset(used_types):
            new.append({"type": "all_types", "date": now})

    return new


def update(
    challenge_id: int,
    score: int,
    topic: str,
    difficulty: str,
    hint_used: bool = False,
    question: str = "",
    human_answer: str = "",
    correct_answer: str = "",
    feedback: str = "",
    context: str = "",
):
    with open(PROFILE_PATH) as f:
        profile = json.load(f)

    # Update streak
    if score >= 2:
        profile["current_streak"] += 1
    elif score == 0:
        profile["current_streak"] = 0
    # score == 1: no change
    profile["best_streak"] = max(profile["best_streak"], profile["current_streak"])

    # Calculate XP
    xp = calculate_xp(score, difficulty, profile["current_streak"], hint_used)

    # Update totals
    profile["total_xp"] += xp
    profile["total_challenges"] += 1
    profile["scores"][str(score)] = profile["scores"].get(str(score), 0) + 1
    profile["overall_level"] = get_overall_level(profile["total_xp"])

    # Update topic
    if topic not in profile["topics"]:
        profile["topics"][topic] = {"attempts": 0, "scores": [], "level": "Apprentice"}
    profile["topics"][topic]["attempts"] += 1
    profile["topics"][topic]["scores"].append(score)
    # Keep last 50 for storage efficiency
    if len(profile["topics"][topic]["scores"]) > 50:
        profile["topics"][topic]["scores"] = profile["topics"][topic]["scores"][-50:]
    profile["topics"][topic]["level"] = get_topic_level(profile["topics"][topic])
    profile["topics"][topic]["last_challenged"] = datetime.now(timezone.utc).isoformat()

    # Increment challenge ID
    profile["next_challenge_id"] = challenge_id + 1

    # Check milestones
    new_milestones = check_milestones(profile, score, topic)
    profile["milestones"].extend(new_milestones)

    # Save
    with open(PROFILE_PATH, "w") as f:
        json.dump(profile, f, indent=2)

    return {
        "xp_earned": xp,
        "new_total_xp": profile["total_xp"],
        "streak": profile["current_streak"],
        "overall_level": profile["overall_level"],
        "topic_level": profile["topics"][topic]["level"],
        "new_milestones": new_milestones,
    }


if __name__ == "__main__":
    # CLI: python update_score.py <challenge_id> <score> <topic> <difficulty> [hint_used]
    result = update(
        challenge_id=int(sys.argv[1]),
        score=int(sys.argv[2]),
        topic=sys.argv[3],
        difficulty=sys.argv[4],
        hint_used=sys.argv[5].lower() == "true" if len(sys.argv) > 5 else False,
    )
    print(json.dumps(result, indent=2))
