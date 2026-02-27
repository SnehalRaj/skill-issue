#!/usr/bin/env python3
"""ASCII visualization for the knowledge graph."""

import os
import sys
from skill_issue.knowledge_state import (
    load_graph,
    load_state,
    get_all_nodes,
    get_weak_nodes,
    get_node_priority,
    init_domain,
)

# ANSI color codes
COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "white": "\033[97m",
    "grey": "\033[90m",
}


def supports_color() -> bool:
    """Check if terminal supports ANSI colors."""
    if os.environ.get("NO_COLOR"):
        return False
    if not hasattr(sys.stdout, "isatty"):
        return False
    if not sys.stdout.isatty():
        return False
    return True


def c(color: str, text: str) -> str:
    """Colorize text if terminal supports it."""
    if not supports_color():
        return text
    return f"{COLORS.get(color, '')}{text}{COLORS['reset']}"


def status_color(status: str) -> str:
    """Get color for a status."""
    return {
        "mastered": "green",
        "strong": "cyan",
        "developing": "yellow",
        "weak": "red",
    }.get(status, "grey")


def status_prefix(status: str) -> str:
    """Get prefix icon for a status."""
    return {
        "mastered": "[MASTERED]",
        "strong": "[STRONG]  ",
        "developing": "[GOOD]    ",
        "weak": "[WEAK]    ",
    }.get(status, "[UNSEEN]  ")


def ascii_graph(domain: str, bar_width: int = 30) -> str:
    """
    Generate ASCII visualization of knowledge graph mastery.

    Shows each node as a bar with status prefix, filled portion, and score.
    """
    lines = []

    # Header
    lines.append(c("bold", f"Knowledge Graph: {domain}"))
    lines.append("=" * 60)
    lines.append("")

    # Get all nodes
    nodes = get_all_nodes(domain)
    if not nodes:
        lines.append(c("dim", "No nodes found. Run: skill-issue graph init --domain " + domain))
        return "\n".join(lines)

    # Sort by reuse_weight descending (most important first)
    nodes.sort(key=lambda x: -x[1]["reuse_weight"])

    # Node bars
    for node_id, node_info, node_state in nodes:
        mastery = node_state["mastery"]
        status = node_state["status"]
        attempts = node_state["attempts"]
        reuse_weight = node_info["reuse_weight"]

        # Build the bar
        filled = int(mastery * bar_width)
        empty = bar_width - filled

        # Bar characters
        bar = "█" * filled + "░" * empty

        # Color the bar based on status
        color = status_color(status)
        prefix = status_prefix(status)

        # Format: [STATUS]   node-name          [████████░░░░░░] 0.72 (5)
        name_col = node_id[:22].ljust(22)
        mastery_str = f"{mastery:.2f}"
        attempts_str = f"({attempts})" if attempts > 0 else ""

        line = f"{c(color, prefix)} {name_col} [{c(color, bar)}] {mastery_str} {c('dim', attempts_str)}"
        lines.append(line)

    # Priority Queue Section
    lines.append("")
    lines.append(c("bold", "Priority Queue (work on these next):"))
    lines.append("-" * 60)

    weak_nodes = get_weak_nodes(domain, top_n=5)
    for node_id, priority, node_info, node_state in weak_nodes:
        mastery = node_state["mastery"]
        reuse_weight = node_info["reuse_weight"]
        gap = 1.0 - mastery

        # Format: ▶ node-id (priority: 0.85 = weight:0.95 × gap:0.90)
        line = f"  {c('yellow', '▶')} {node_id}"
        detail = f"priority: {priority:.2f} = weight:{reuse_weight:.2f} × gap:{gap:.2f}"
        line += f"  {c('dim', '(' + detail + ')')}"
        lines.append(line)

    # Summary
    lines.append("")
    lines.append("-" * 60)
    total_mastery = sum(n[2]["mastery"] for n in nodes)
    avg_mastery = total_mastery / len(nodes) if nodes else 0
    mastered = sum(1 for n in nodes if n[2]["status"] == "mastered")
    strong = sum(1 for n in nodes if n[2]["status"] == "strong")
    weak = sum(1 for n in nodes if n[2]["status"] == "weak")

    lines.append(f"Total nodes: {len(nodes)} | Avg mastery: {c('cyan', f'{avg_mastery:.2f}')}")
    lines.append(f"  {c('green', f'{mastered} mastered')} | {c('cyan', f'{strong} strong')} | {c('red', f'{weak} weak')}")

    return "\n".join(lines)


def ascii_weak_list(domain: str, top_n: int = 5) -> str:
    """Generate a simple list of weak/priority nodes."""
    lines = []

    weak_nodes = get_weak_nodes(domain, top_n=top_n)
    if not weak_nodes:
        lines.append("No weak nodes found.")
        return "\n".join(lines)

    lines.append(c("bold", f"Top {top_n} Priority Nodes ({domain}):"))
    lines.append("")

    for i, (node_id, priority, node_info, node_state) in enumerate(weak_nodes, 1):
        mastery = node_state["mastery"]
        status = node_state["status"]
        name = node_info["name"]

        lines.append(f"  {i}. {c('yellow', node_id)}")
        lines.append(f"     {c('dim', name)}")
        lines.append(f"     Priority: {priority:.2f} | Mastery: {mastery:.2f} | Status: {status}")

        # Show first challenge hook
        hooks = node_info.get("challenge_hooks", [])
        if hooks:
            lines.append(f"     {c('dim', '→ ' + hooks[0])}")
        lines.append("")

    return "\n".join(lines)


def weak_nodes_json(domain: str, top_n: int = 5) -> list:
    """Return weak nodes as JSON-serializable list."""
    weak_nodes = get_weak_nodes(domain, top_n=top_n)
    result = []

    for node_id, priority, node_info, node_state in weak_nodes:
        result.append({
            "id": node_id,
            "name": node_info["name"],
            "priority": round(priority, 3),
            "mastery": round(node_state["mastery"], 3),
            "reuse_weight": node_info["reuse_weight"],
            "status": node_state["status"],
            "challenge_hooks": node_info.get("challenge_hooks", []),
        })

    return result


if __name__ == "__main__":
    import sys
    domain = sys.argv[1] if len(sys.argv) > 1 else "quantum-ml"
    print(ascii_graph(domain))
