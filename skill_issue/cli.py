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
    # Run onboarding interview if no domain specified
    if not args.domains:
        from skill_issue.onboarding import run_onboarding
        from skill_issue.knowledge_state import KnowledgeState
        domains = run_onboarding()
        init_profile(
            username=args.name or os.environ.get("USER", "human"),
            domains=domains,
            force=getattr(args, "force", False),
        )
        # Auto-init knowledge state for inferred domains
        ks = KnowledgeState()
        for domain in domains:
            try:
                ks.init_domain(domain)
            except Exception:
                pass
    else:
        domains = args.domains.split(",")
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


# --- Knowledge Graph Commands ---

def cmd_graph_show(args):
    """Show ASCII visualization of knowledge graph."""
    from skill_issue.graph_viz import ascii_graph
    from skill_issue.knowledge_state import list_domains
    domain = args.domain
    if domain not in list_domains():
        print(f"Domain '{domain}' not found. Available: {', '.join(list_domains())}")
        sys.exit(1)
    print(ascii_graph(domain))


def cmd_graph_weak(args):
    """Show top priority (weak + high reuse_weight) nodes."""
    from skill_issue.knowledge_state import list_domains
    domain = args.domain
    if domain not in list_domains():
        print(f"Domain '{domain}' not found. Available: {', '.join(list_domains())}")
        sys.exit(1)

    if args.json:
        from skill_issue.graph_viz import weak_nodes_json
        print(json.dumps(weak_nodes_json(domain, top_n=args.top), indent=2))
    else:
        from skill_issue.graph_viz import ascii_weak_list
        print(ascii_weak_list(domain, top_n=args.top))


def cmd_graph_update(args):
    """Update mastery for a specific node."""
    from skill_issue.knowledge_state import update_node, list_domains
    domain = args.domain
    if domain not in list_domains():
        print(f"Domain '{domain}' not found. Available: {', '.join(list_domains())}")
        sys.exit(1)

    result = update_node(domain, args.node, args.score)
    print(f"Updated {args.node}:")
    print(f"  Mastery: {result['mastery']:.2f}")
    print(f"  Status:  {result['status']}")
    print(f"  Attempts: {result['attempts']}")


def cmd_graph_init(args):
    """Initialize user state for a domain."""
    from skill_issue.knowledge_state import init_domain, load_graph, list_domains
    domain = args.domain
    if domain not in list_domains():
        print(f"Domain '{domain}' not found. Available: {', '.join(list_domains())}")
        sys.exit(1)

    init_domain(domain)
    graph = load_graph(domain)
    print(f"Initialized knowledge state for '{domain}'")
    print(f"  Nodes: {len(graph['nodes'])}")
    print(f"  State saved to: ~/.skill-issue/knowledge_state.json")


def cmd_graph_web(args):
    """Generate D3 web visualization and open in browser."""
    from skill_issue.knowledge_state import list_domains, get_all_nodes, load_graph
    from skill_issue.web_viz import generate_html
    import tempfile
    import webbrowser

    domain = args.domain
    if domain not in list_domains():
        print(f"Domain '{domain}' not found. Available: {', '.join(list_domains())}")
        sys.exit(1)

    html = generate_html(domain)

    # Write to temp file and open
    output_path = args.output
    if not output_path:
        fd, output_path = tempfile.mkstemp(suffix=".html", prefix=f"skill-issue-{domain}-")
        os.close(fd)

    with open(output_path, "w") as f:
        f.write(html)

    print(f"Generated: {output_path}")
    if not args.no_open:
        webbrowser.open(f"file://{output_path}")


def cmd_graph_decay(args):
    """Apply decay to all nodes (for testing)."""
    from skill_issue.knowledge_state import apply_decay
    state = apply_decay()
    domains_updated = len(state.get("domains", {}))
    print(f"Applied decay to {domains_updated} domain(s)")


def cmd_graph_domains(args):
    """List available knowledge graph domains."""
    from skill_issue.onboarding import print_available_domains
    print_available_domains()


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

    # graph (with subcommands)
    p_graph = sub.add_parser("graph", help="Knowledge graph commands")
    graph_sub = p_graph.add_subparsers(dest="graph_command", metavar="<subcommand>")

    # graph show
    p_graph_show = graph_sub.add_parser("show", help="Show ASCII visualization")
    p_graph_show.add_argument("--domain", default="quantum-ml", help="Domain (default: quantum-ml)")
    p_graph_show.set_defaults(func=cmd_graph_show)

    # graph weak
    p_graph_weak = graph_sub.add_parser("weak", help="Show top priority nodes")
    p_graph_weak.add_argument("--domain", default="quantum-ml", help="Domain (default: quantum-ml)")
    p_graph_weak.add_argument("--top", type=int, default=5, help="Number of nodes (default: 5)")
    p_graph_weak.add_argument("--json", action="store_true", help="Output as JSON")
    p_graph_weak.set_defaults(func=cmd_graph_weak)

    # graph update
    p_graph_update = graph_sub.add_parser("update", help="Update node mastery")
    p_graph_update.add_argument("--node", required=True, help="Node ID")
    p_graph_update.add_argument("--score", type=int, required=True, choices=[0, 1, 2, 3])
    p_graph_update.add_argument("--domain", required=True, help="Domain")
    p_graph_update.set_defaults(func=cmd_graph_update)

    # graph init
    p_graph_init = graph_sub.add_parser("init", help="Initialize domain state")
    p_graph_init.add_argument("--domain", required=True, help="Domain to initialize")
    p_graph_init.set_defaults(func=cmd_graph_init)

    # graph web
    p_graph_web = graph_sub.add_parser("web", help="Generate D3 web visualization")
    p_graph_web.add_argument("--domain", default="quantum-ml", help="Domain (default: quantum-ml)")
    p_graph_web.add_argument("--output", help="Output HTML file path")
    p_graph_web.add_argument("--no-open", action="store_true", help="Don't open in browser")
    p_graph_web.set_defaults(func=cmd_graph_web)

    # graph decay
    p_graph_decay = graph_sub.add_parser("decay", help="Apply decay (testing)")
    p_graph_decay.set_defaults(func=cmd_graph_decay)

    # graph domains
    p_graph_domains = graph_sub.add_parser("domains", help="List available domains")
    p_graph_domains.set_defaults(func=cmd_graph_domains)

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

    if args.command == "graph" and not getattr(args, "graph_command", None):
        p_graph.print_help()
        return

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
