#!/usr/bin/env python3
"""skill-issue CLI — main entry point."""

import argparse
import json
import os
import sys
from pathlib import Path


def cmd_init(args):
    """Initialize ~/.skill-issue/ profile."""
    from skill_issue.init_profile import init_profile
    domains = args.domains.split(",") if args.domains else ["algorithms", "debugging", "design"]
    init_profile(
        username=args.name or os.environ.get("USER", "human"),
        domains=domains,
        force=getattr(args, "force", False),
    )

    skill_md_path = Path(__file__).parent.parent / "SKILL.md"

    if args.claude:
        _inject_into_file("CLAUDE.md", skill_md_path)
    elif args.cursor:
        _inject_into_file(".cursorrules", skill_md_path)
    elif args.print_only:
        if skill_md_path.exists():
            print("\n" + "─" * 60)
            print("Paste this into your editor's system prompt / rules file:")
            print("─" * 60)
            print(skill_md_path.read_text())
    else:
        print("\nNext step — activate in your editor:")
        print("  Claude Code:  skill-issue init --claude")
        print("  Cursor:       skill-issue init --cursor")
        print("  Other:        skill-issue init --print")


def _inject_into_file(filename: str, skill_md_path: Path):
    """Append skill-issue activation block to a config file."""
    target = Path.cwd() / filename
    marker = "<!-- skill-issue -->"
    skill_block = f"\n{marker}\n"

    if skill_md_path.exists():
        skill_block += f"\n{skill_md_path.read_text().strip()}\n"
    else:
        skill_block += "\n# skill-issue active — gamified challenges enabled\n"

    if target.exists():
        content = target.read_text()
        if marker in content:
            print(f"skill-issue already active in {filename}")
            return
        target.write_text(content + skill_block)
    else:
        target.write_text(skill_block.lstrip())

    print(f"✓ skill-issue injected into {filename}")
    print(f"  Open a Claude Code session in this directory — challenges will start automatically.")


def cmd_score(args):
    """Score a challenge and update profile."""
    from skill_issue.update_score import update
    result = update(
        challenge_id=args.id,
        score=args.score,
        topic=args.topic,
        difficulty=args.difficulty,
        hint_used=args.hint,
    )
    print(f"\nScore: {args.score}/3")
    print(f"XP earned: +{result['xp_earned']} | Total: {result['new_total_xp']}")
    print(f"Streak: {result['streak']} | Level: {result['overall_level']}")
    print(f"Topic level ({args.topic}): {result['topic_level']}")
    if result["new_milestones"]:
        for m in result["new_milestones"]:
            label = {
                "first_challenge": "First challenge completed! 🎯",
                "streak_5": "5 in a row! 🔥🔥",
                "streak_10": "10-streak! 🔥🔥🔥",
                "topic_expert": f"{m.get('topic')} Expert unlocked! 🔷",
                "topic_master": f"{m.get('topic')} MASTERED! ⭐",
                "xp_500": "500 XP! 💎",
                "xp_2000": "2000 XP! 💎💎",
                "xp_5000": "5000 XP! 💎💎💎",
            }.get(m["type"], m["type"])
            print(f"\n🏆 {label}")


def cmd_stats(args):
    """Show current profile stats."""
    skill_dir = Path.home() / ".skill-issue"
    profile_path = skill_dir / "profile.json"
    if not profile_path.exists():
        print("No profile found. Run: skill-issue init")
        sys.exit(1)
    with open(profile_path) as f:
        p = json.load(f)
    total = p["total_challenges"]
    correct = p["scores"].get("2", 0) + p["scores"].get("3", 0)
    accuracy = (correct / total * 100) if total > 0 else 0
    print(f"\n🧠 skill-issue — {p['username']}")
    print(f"Level:    {p['overall_level']} ({p['total_xp']} XP)")
    print(f"Streak:   🔥 {p['current_streak']} (best: {p['best_streak']})")
    print(f"Accuracy: {accuracy:.0f}%  ({correct}/{total} correct)")
    if p["topics"]:
        print("\nTopics:")
        for topic, data in sorted(p["topics"].items(), key=lambda x: -x[1]["attempts"]):
            print(f"  {topic}: {data['level']} ({data['attempts']} attempts)")


def cmd_report(args):
    """Regenerate leaderboard.md trophy wall."""
    from skill_issue.generate_report import generate
    generate()


def cmd_export(args):
    """Export history to JSON or CSV."""
    from skill_issue.export_stats import export_json, export_csv
    if args.format == "csv":
        export_csv(args.output)
    else:
        export_json(args.output)


def main():
    parser = argparse.ArgumentParser(
        prog="skill-issue",
        description="Gamified active learning for agentic coding sessions",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    # init
    p_init = sub.add_parser("init", help="Set up your ~/.skill-issue/ profile")
    p_init.add_argument("--name", help="Your name (default: $USER)")
    p_init.add_argument("--domains", default="quantum,ml,algorithms",
                        help="Comma-separated domains (default: quantum,ml,algorithms)")
    p_init.add_argument("--force", action="store_true", help="Overwrite existing profile")
    p_init.add_argument("--claude", action="store_true", help="Auto-inject into CLAUDE.md (Claude Code)")
    p_init.add_argument("--cursor", action="store_true", help="Auto-inject into .cursorrules (Cursor)")
    p_init.add_argument("--print", dest="print_only", action="store_true", help="Print SKILL.md to paste manually")
    p_init.set_defaults(func=cmd_init)

    # score
    p_score = sub.add_parser("score", help="Record a challenge result")
    p_score.add_argument("--id", type=int, required=True, help="Challenge ID")
    p_score.add_argument("--score", type=int, required=True, choices=[0, 1, 2, 3])
    p_score.add_argument("--topic", required=True, help="Topic tag (e.g. quantum-circuits)")
    p_score.add_argument("--difficulty", required=True,
                         choices=["Apprentice", "Practitioner", "Expert", "Master"])
    p_score.add_argument("--hint", action="store_true", help="Hint was used")
    p_score.set_defaults(func=cmd_score)

    # stats
    p_stats = sub.add_parser("stats", help="Show your current stats")
    p_stats.set_defaults(func=cmd_stats)

    # report
    p_report = sub.add_parser("report", help="Regenerate leaderboard.md trophy wall")
    p_report.set_defaults(func=cmd_report)

    # export
    p_export = sub.add_parser("export", help="Export history")
    p_export.add_argument("--format", choices=["json", "csv"], default="json")
    p_export.add_argument("--output", help="Output file path")
    p_export.set_defaults(func=cmd_export)

    args = parser.parse_args()

    if not args.command:
        # Default: show stats if profile exists, else prompt init
        skill_dir = Path.home() / ".skill-issue"
        if (skill_dir / "profile.json").exists():
            cmd_stats(args)
        else:
            print("Welcome to skill-issue 🧠")
            print("Get started: skill-issue init")
        return

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
