#!/usr/bin/env python3
"""Knowledge state management for the pedagogical knowledge graph."""

import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

SKILL_DIR = Path.home() / ".skill-issue"
KNOWLEDGE_STATE_PATH = SKILL_DIR / "knowledge_state.json"
GRAPHS_DIR = Path(__file__).parent.parent / "references" / "knowledge_graphs"

# EMA smoothing factor: weight recent scores more heavily
EMA_ALPHA = 0.3

# Decay settings
DECAY_GRACE_DAYS = 3
DECAY_RATE_PER_DAY = 0.02

# Mastery thresholds
MASTERY_THRESHOLDS = {
    "mastered": 0.85,
    "strong": 0.70,
    "developing": 0.40,
    "weak": 0.0,
}


def load_graph(domain: str) -> dict:
    """Load a knowledge graph from JSON."""
    graph_path = GRAPHS_DIR / f"{domain}.json"
    if not graph_path.exists():
        raise FileNotFoundError(f"Knowledge graph not found: {domain}")
    with open(graph_path) as f:
        return json.load(f)


def list_domains() -> list:
    """List available knowledge graph domains."""
    return [p.stem for p in GRAPHS_DIR.glob("*.json")]


def load_state() -> dict:
    """Load user knowledge state from disk."""
    if not KNOWLEDGE_STATE_PATH.exists():
        return {"version": 1, "domains": {}}
    with open(KNOWLEDGE_STATE_PATH) as f:
        return json.load(f)


def save_state(state: dict):
    """Save user knowledge state to disk."""
    SKILL_DIR.mkdir(parents=True, exist_ok=True)
    with open(KNOWLEDGE_STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


def init_domain(domain: str) -> dict:
    """Initialize user state for a domain from its knowledge graph."""
    graph = load_graph(domain)
    state = load_state()

    if domain not in state["domains"]:
        state["domains"][domain] = {"nodes": {}}

    now = datetime.now(timezone.utc).isoformat()
    for node in graph["nodes"]:
        node_id = node["id"]
        if node_id not in state["domains"][domain]["nodes"]:
            state["domains"][domain]["nodes"][node_id] = {
                "mastery": 0.0,
                "attempts": 0,
                "last_seen": None,
                "status": "weak",
            }

    save_state(state)
    return state["domains"][domain]


def get_node_state(domain: str, node_id: str) -> dict:
    """Get state for a specific node."""
    state = load_state()
    if domain not in state["domains"]:
        return None
    return state["domains"][domain]["nodes"].get(node_id)


def get_node_priority(domain: str, node_id: str) -> float:
    """
    Calculate priority for a node: reuse_weight * (1 - mastery).
    Higher priority = more important to learn and lower current mastery.
    """
    graph = load_graph(domain)
    node_info = next((n for n in graph["nodes"] if n["id"] == node_id), None)
    if not node_info:
        return 0.0

    state = load_state()
    if domain not in state["domains"]:
        return node_info["reuse_weight"]  # Full priority if unseen

    node_state = state["domains"][domain]["nodes"].get(node_id)
    if not node_state:
        return node_info["reuse_weight"]

    return node_info["reuse_weight"] * (1.0 - node_state["mastery"])


def update_node(domain: str, node_id: str, score: int):
    """
    Update node mastery using exponential moving average.
    Score: 0-3 (same as challenge scoring)
    """
    state = load_state()

    if domain not in state["domains"]:
        init_domain(domain)
        state = load_state()

    if node_id not in state["domains"][domain]["nodes"]:
        state["domains"][domain]["nodes"][node_id] = {
            "mastery": 0.0,
            "attempts": 0,
            "last_seen": None,
            "status": "weak",
        }

    node = state["domains"][domain]["nodes"][node_id]

    # Convert score (0-3) to mastery delta (0.0-1.0)
    # 0 = wrong, 1 = partial, 2 = correct, 3 = exceptional
    score_to_mastery = {0: 0.0, 1: 0.3, 2: 0.7, 3: 1.0}
    new_observation = score_to_mastery.get(score, 0.0)

    # EMA update: mastery = alpha * new + (1-alpha) * old
    old_mastery = node["mastery"]
    node["mastery"] = EMA_ALPHA * new_observation + (1 - EMA_ALPHA) * old_mastery

    # Clamp to [0, 1]
    node["mastery"] = max(0.0, min(1.0, node["mastery"]))

    node["attempts"] += 1
    node["last_seen"] = datetime.now(timezone.utc).isoformat()
    node["status"] = _compute_status(node["mastery"])

    save_state(state)
    return node


def _compute_status(mastery: float) -> str:
    """Compute status label from mastery value."""
    if mastery >= MASTERY_THRESHOLDS["mastered"]:
        return "mastered"
    elif mastery >= MASTERY_THRESHOLDS["strong"]:
        return "strong"
    elif mastery >= MASTERY_THRESHOLDS["developing"]:
        return "developing"
    else:
        return "weak"


def apply_decay():
    """
    Apply gentle decay to all nodes not seen recently.
    Grace period of DECAY_GRACE_DAYS, then DECAY_RATE_PER_DAY after.
    """
    state = load_state()
    now = datetime.now(timezone.utc)
    modified = False

    for domain in state["domains"]:
        for node_id, node in state["domains"][domain]["nodes"].items():
            if node["last_seen"] is None:
                continue

            last_seen = datetime.fromisoformat(node["last_seen"].replace("Z", "+00:00"))
            days_since = (now - last_seen).days

            if days_since > DECAY_GRACE_DAYS:
                decay_days = days_since - DECAY_GRACE_DAYS
                decay_amount = decay_days * DECAY_RATE_PER_DAY

                old_mastery = node["mastery"]
                node["mastery"] = max(0.0, old_mastery - decay_amount)
                node["status"] = _compute_status(node["mastery"])
                modified = True

    if modified:
        save_state(state)

    return state


def get_weak_nodes(domain: str, top_n: int = 5) -> list:
    """
    Get top N highest priority nodes (weak + high reuse_weight).
    Returns list of (node_id, priority, node_info, node_state) tuples.
    """
    graph = load_graph(domain)
    state = load_state()

    if domain not in state["domains"]:
        init_domain(domain)
        state = load_state()

    results = []
    for node in graph["nodes"]:
        node_id = node["id"]
        priority = get_node_priority(domain, node_id)
        node_state = state["domains"][domain]["nodes"].get(node_id, {
            "mastery": 0.0,
            "attempts": 0,
            "last_seen": None,
            "status": "weak",
        })
        results.append((node_id, priority, node, node_state))

    # Sort by priority descending
    results.sort(key=lambda x: -x[1])
    return results[:top_n]


def get_strong_nodes(domain: str) -> list:
    """
    Get all nodes with mastery > 0.8.
    Returns list of (node_id, node_info, node_state) tuples.
    """
    graph = load_graph(domain)
    state = load_state()

    if domain not in state["domains"]:
        return []

    results = []
    for node in graph["nodes"]:
        node_id = node["id"]
        node_state = state["domains"][domain]["nodes"].get(node_id)
        if node_state and node_state["mastery"] > 0.8:
            results.append((node_id, node, node_state))

    return results


def map_code_to_nodes(code_snippet: str, domain: str) -> list:
    """
    Map code snippet to relevant knowledge nodes via keyword/alias matching.
    Returns list of (node_id, node_info, match_count) tuples.
    """
    graph = load_graph(domain)
    code_lower = code_snippet.lower()

    results = []
    for node in graph["nodes"]:
        matches = 0

        # Check node name
        if node["name"].lower() in code_lower:
            matches += 2

        # Check node id (often kebab-case)
        if node["id"].replace("-", "_") in code_lower or node["id"].replace("-", " ") in code_lower:
            matches += 2

        # Check aliases
        for alias in node.get("aliases", []):
            alias_lower = alias.lower()
            # Word boundary matching for short aliases
            if len(alias) <= 4:
                pattern = r'\b' + re.escape(alias_lower) + r'\b'
                if re.search(pattern, code_lower):
                    matches += 1
            elif alias_lower in code_lower:
                matches += 1

        if matches > 0:
            results.append((node["id"], node, matches))

    # Sort by match count descending
    results.sort(key=lambda x: -x[2])
    return results


def get_all_nodes(domain: str) -> list:
    """
    Get all nodes with their state for a domain.
    Returns list of (node_id, node_info, node_state) tuples.
    """
    graph = load_graph(domain)
    state = load_state()

    if domain not in state["domains"]:
        init_domain(domain)
        state = load_state()

    results = []
    for node in graph["nodes"]:
        node_id = node["id"]
        node_state = state["domains"][domain]["nodes"].get(node_id, {
            "mastery": 0.0,
            "attempts": 0,
            "last_seen": None,
            "status": "weak",
        })
        results.append((node_id, node, node_state))

    return results


if __name__ == "__main__":
    # Quick test
    import sys
    if len(sys.argv) > 1:
        domain = sys.argv[1]
        print(f"Testing domain: {domain}")
        print(f"Available domains: {list_domains()}")
        init_domain(domain)
        print(f"\nTop 5 weak nodes:")
        for node_id, priority, node, state in get_weak_nodes(domain, 5):
            print(f"  {node_id}: priority={priority:.2f}, mastery={state['mastery']:.2f}")
