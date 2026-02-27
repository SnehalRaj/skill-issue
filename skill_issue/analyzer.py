#!/usr/bin/env python3
"""
Retroactive knowledge bootstrap analyzer.

Scans Claude Code session history (JSONL files) and infers initial mastery scores
based on conversation patterns — questions indicate weakness, assertions indicate strength.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from skill_issue.knowledge_state import (
    load_graph,
    load_state,
    save_state,
    init_domain,
    list_domains,
    SKILL_DIR,
)


# Claude Code session storage location
CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"

# Question markers indicating uncertainty/weakness
QUESTION_MARKERS = [
    r"\bwhat is\b",
    r"\bhow does\b",
    r"\bcan you explain\b",
    r"\bwhy does\b",
    r"\bi don'?t understand\b",
    r"\bhelp me understand\b",
    r"\bwhat'?s the difference\b",
    r"\bi'?m confused about\b",
    r"\bwhat does .+ mean\b",
    r"\bcan you help me\b",
    r"\bi'?m not sure\b",
    r"\bwhat'?s .+ for\b",
    r"\bhow do (i|you|we)\b",
    r"\bwhy is\b",
    r"\bwhy do\b",
    r"\?$",  # Ends with question mark
]

# Confidence markers indicating strength
CONFIDENCE_MARKERS = [
    r"^```",  # Code blocks (user sharing code they wrote)
    r"\bi implemented\b",
    r"\bi wrote\b",
    r"\bi built\b",
    r"\bi created\b",
    r"\bi fixed\b",
    r"\bhere'?s my\b",
    r"\blet me show you\b",
    r"\bthis is how\b",
]


def find_project_sessions(project_path: Optional[Path] = None) -> list[Path]:
    """
    Find all JSONL session files for a project.

    If project_path is None, searches current working directory's project folder.
    """
    if not CLAUDE_PROJECTS_DIR.exists():
        return []

    if project_path is None:
        project_path = Path.cwd()

    # Claude Code uses a mangled path format: /Users/foo/bar -> -Users-foo-bar
    mangled = str(project_path).replace("/", "-")
    if mangled.startswith("-"):
        mangled = mangled  # Already starts with dash, that's correct
    else:
        mangled = "-" + mangled

    project_dir = CLAUDE_PROJECTS_DIR / mangled
    if not project_dir.exists():
        return []

    return sorted(project_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)


def find_all_sessions() -> list[Path]:
    """Find all JSONL session files across all projects."""
    if not CLAUDE_PROJECTS_DIR.exists():
        return []

    sessions = []
    for project_dir in CLAUDE_PROJECTS_DIR.iterdir():
        if project_dir.is_dir():
            sessions.extend(project_dir.glob("*.jsonl"))

    return sorted(sessions, key=lambda p: p.stat().st_mtime, reverse=True)


def extract_messages(session_path: Path) -> list[dict]:
    """
    Extract user and assistant messages from a session JSONL file.

    Returns list of dicts with keys: role, text, timestamp
    """
    messages = []

    try:
        with open(session_path, "r") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    msg_type = obj.get("type")

                    if msg_type not in ("user", "assistant"):
                        continue

                    message = obj.get("message", {})
                    content = message.get("content", "")
                    timestamp = obj.get("timestamp", "")

                    # Handle content that can be string or list
                    text = ""
                    if isinstance(content, str):
                        text = content
                    elif isinstance(content, list):
                        # Extract text from content blocks
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                text += block.get("text", "") + "\n"

                    if text.strip():
                        messages.append({
                            "role": msg_type,
                            "text": text.strip(),
                            "timestamp": timestamp,
                        })

                except json.JSONDecodeError:
                    continue
    except Exception:
        return []

    return messages


def detect_concepts_in_text(text: str, domain: str) -> list[str]:
    """
    Detect which concepts from a domain's knowledge graph appear in text.

    Returns list of node IDs that were detected.
    """
    try:
        graph = load_graph(domain)
    except FileNotFoundError:
        return []

    text_lower = text.lower()
    detected = []

    for node in graph["nodes"]:
        node_id = node["id"]
        matches = False

        # Check node name
        if node["name"].lower() in text_lower:
            matches = True

        # Check node id (kebab-case variants)
        id_variants = [
            node_id.lower(),
            node_id.replace("-", " "),
            node_id.replace("-", "_"),
        ]
        for variant in id_variants:
            if variant in text_lower:
                matches = True
                break

        # Check aliases
        for alias in node.get("aliases", []):
            alias_lower = alias.lower()
            if len(alias) <= 3:
                # Short aliases need word boundaries
                pattern = r'\b' + re.escape(alias_lower) + r'\b'
                if re.search(pattern, text_lower):
                    matches = True
                    break
            elif alias_lower in text_lower:
                matches = True
                break

        if matches:
            detected.append(node_id)

    return detected


def classify_message_intent(text: str) -> str:
    """
    Classify whether a user message indicates a question/weakness or assertion/strength.

    Returns: "question", "assertion", or "neutral"
    """
    text_lower = text.lower()

    # Check question markers
    question_count = 0
    for pattern in QUESTION_MARKERS:
        if re.search(pattern, text_lower):
            question_count += 1

    # Check confidence markers
    confidence_count = 0
    for pattern in CONFIDENCE_MARKERS:
        if re.search(pattern, text_lower, re.MULTILINE):
            confidence_count += 1

    # Classify based on marker counts
    if question_count > confidence_count:
        return "question"
    elif confidence_count > 0:
        return "assertion"
    else:
        return "neutral"


def analyze_sessions(
    sessions: list[Path],
    domains: list[str],
    max_sessions: int = 50,
) -> dict[str, dict[str, dict]]:
    """
    Analyze session history and compute concept scores.

    Returns: {domain: {node_id: {"score": float, "signals": list}}}

    Scoring rules per concept:
    - User question mentioning concept: -0.15 (weakness signal)
    - User assertion/code mentioning concept: +0.20 (strength signal)
    - Claude-only mention (user didn't mention): +0.05 (neutral/slight positive)
    - Final score clamped to [0.0, 0.8]
    """
    results = {domain: {} for domain in domains}

    for session_path in sessions[:max_sessions]:
        messages = extract_messages(session_path)

        # Group consecutive messages to understand context
        for i, msg in enumerate(messages):
            if msg["role"] != "user":
                continue

            user_text = msg["text"]
            intent = classify_message_intent(user_text)

            # Find Claude's response (if any)
            claude_text = ""
            if i + 1 < len(messages) and messages[i + 1]["role"] == "assistant":
                claude_text = messages[i + 1]["text"]

            for domain in domains:
                # Detect concepts in user message
                user_concepts = detect_concepts_in_text(user_text, domain)

                # Detect concepts only in Claude's response (not user's)
                claude_concepts = detect_concepts_in_text(claude_text, domain)
                claude_only = [c for c in claude_concepts if c not in user_concepts]

                # Score user-mentioned concepts based on intent
                for concept in user_concepts:
                    if concept not in results[domain]:
                        results[domain][concept] = {"score": 0.0, "signals": []}

                    if intent == "question":
                        results[domain][concept]["score"] -= 0.15
                        results[domain][concept]["signals"].append("question")
                    elif intent == "assertion":
                        results[domain][concept]["score"] += 0.20
                        results[domain][concept]["signals"].append("assertion")
                    else:
                        results[domain][concept]["score"] += 0.05
                        results[domain][concept]["signals"].append("neutral_user")

                # Claude-only mentions: slight positive (user learned something)
                for concept in claude_only:
                    if concept not in results[domain]:
                        results[domain][concept] = {"score": 0.0, "signals": []}
                    results[domain][concept]["score"] += 0.05
                    results[domain][concept]["signals"].append("claude_explained")

    # Clamp all scores to [0.0, 0.8]
    for domain in results:
        for concept in results[domain]:
            raw = results[domain][concept]["score"]
            results[domain][concept]["score"] = max(0.0, min(0.8, raw))

    return results


def apply_analysis_to_state(analysis: dict[str, dict[str, dict]]) -> dict:
    """
    Apply analyzed scores to the knowledge state.

    Only updates nodes that have signals (detected mentions).
    Returns the updated state.
    """
    state = load_state()
    now = datetime.now(timezone.utc).isoformat()

    for domain, concepts in analysis.items():
        if not concepts:
            continue

        # Initialize domain if needed
        if domain not in state["domains"]:
            try:
                init_domain(domain)
                state = load_state()
            except FileNotFoundError:
                continue

        for node_id, data in concepts.items():
            if node_id not in state["domains"][domain]["nodes"]:
                continue

            score = data["score"]
            signal_count = len(data["signals"])

            # Only update if we have actual signals
            if signal_count > 0:
                node = state["domains"][domain]["nodes"][node_id]
                node["mastery"] = score
                node["attempts"] = signal_count
                node["last_seen"] = now

                # Compute status from mastery
                if score >= 0.70:
                    node["status"] = "strong"
                elif score >= 0.40:
                    node["status"] = "developing"
                else:
                    node["status"] = "weak"

    save_state(state)
    return state


def run_analysis(
    project_path: Optional[Path] = None,
    all_projects: bool = False,
    domains: Optional[list[str]] = None,
    max_sessions: int = 50,
    dry_run: bool = False,
) -> dict:
    """
    Run the full analysis pipeline.

    Args:
        project_path: Specific project to analyze (default: current directory)
        all_projects: Analyze all projects instead of specific one
        domains: List of domains to analyze (default: all available)
        max_sessions: Maximum number of sessions to analyze
        dry_run: If True, don't apply changes to state

    Returns summary of analysis.
    """
    # Find sessions
    if all_projects:
        sessions = find_all_sessions()
    else:
        sessions = find_project_sessions(project_path)

    if not sessions:
        return {
            "status": "no_sessions",
            "message": "No Claude Code sessions found",
            "sessions_analyzed": 0,
        }

    # Determine domains
    if domains is None:
        domains = list_domains()

    if not domains:
        return {
            "status": "no_domains",
            "message": "No knowledge graph domains found",
            "sessions_analyzed": 0,
        }

    # Run analysis
    analysis = analyze_sessions(sessions, domains, max_sessions)

    # Count concepts with signals
    concepts_detected = 0
    for domain in analysis:
        concepts_detected += len(analysis[domain])

    # Apply to state (unless dry run)
    if not dry_run and concepts_detected > 0:
        apply_analysis_to_state(analysis)

    return {
        "status": "success",
        "sessions_analyzed": min(len(sessions), max_sessions),
        "domains_analyzed": domains,
        "concepts_detected": concepts_detected,
        "analysis": analysis,
        "applied": not dry_run,
    }


def format_analysis_report(result: dict) -> str:
    """Format analysis result as human-readable report."""
    lines = []

    if result["status"] == "no_sessions":
        return "No Claude Code sessions found. Start some conversations first!"

    if result["status"] == "no_domains":
        return "No knowledge graph domains available."

    lines.append(f"Analyzed {result['sessions_analyzed']} session(s)")
    lines.append(f"Detected {result['concepts_detected']} concept(s) across {len(result['domains_analyzed'])} domain(s)")
    lines.append("")

    analysis = result.get("analysis", {})
    for domain in sorted(analysis.keys()):
        concepts = analysis[domain]
        if not concepts:
            continue

        lines.append(f"─── {domain} ───")

        # Sort by score descending
        sorted_concepts = sorted(
            concepts.items(),
            key=lambda x: (-x[1]["score"], x[0])
        )

        for node_id, data in sorted_concepts[:10]:  # Top 10 per domain
            score = data["score"]
            signals = data["signals"]

            # Format score as bar
            bar_len = int(score * 10)
            bar = "█" * bar_len + "░" * (8 - bar_len)

            # Summarize signals
            q_count = signals.count("question")
            a_count = signals.count("assertion")
            n_count = len(signals) - q_count - a_count

            signal_str = ""
            if q_count:
                signal_str += f" -{q_count}q"
            if a_count:
                signal_str += f" +{a_count}a"
            if n_count:
                signal_str += f" ~{n_count}"

            lines.append(f"  {node_id:<25} [{bar}] {score:.2f}{signal_str}")

        if len(concepts) > 10:
            lines.append(f"  ... and {len(concepts) - 10} more")
        lines.append("")

    if result.get("applied"):
        lines.append("✓ Scores applied to knowledge state")
    else:
        lines.append("(dry run — no changes applied)")

    return "\n".join(lines)


if __name__ == "__main__":
    # Quick test
    import sys

    dry_run = "--dry-run" in sys.argv
    all_projects = "--all" in sys.argv

    result = run_analysis(dry_run=dry_run, all_projects=all_projects)
    print(format_analysis_report(result))
