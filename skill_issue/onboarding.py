#!/usr/bin/env python3
"""
Onboarding interview — infers the user's domain(s) from a short conversation.
Runs on first `skill-issue init` when no --domain is specified.
"""

import json
import re
from pathlib import Path

GRAPHS_DIR = Path(__file__).parent.parent / "references" / "knowledge_graphs"

# Keyword → domain mapping (order matters — more specific first)
DOMAIN_SIGNALS = [
    ("quantum-ml",      ["quantum", "qml", "qubit", "circuit", "pennylane", "qiskit", "variational", "vqe", "qaoa"]),
    ("machine-learning",["machine learning", "deep learning", "neural network", "pytorch", "tensorflow", "sklearn", "scikit", "gradient", "model training", "llm", "transformer", "backprop"]),
    ("data-science",    ["data science", "pandas", "numpy", "jupyter", "statistics", "hypothesis", "regression", "classification", "feature engineering", "matplotlib", "seaborn"]),
    ("web-frontend",    ["frontend", "react", "vue", "angular", "svelte", "css", "html", "javascript", "typescript", "dom", "next.js", "tailwind", "webpack"]),
    ("backend-systems", ["backend", "api", "database", "postgres", "mysql", "redis", "microservice", "rest", "graphql", "django", "fastapi", "flask", "express", "spring", "rails"]),
    ("devops",          ["devops", "docker", "kubernetes", "k8s", "terraform", "ci/cd", "github actions", "jenkins", "aws", "gcp", "azure", "infrastructure", "helm", "ansible"]),
    ("design-systems",  ["design", "figma", "ux", "ui", "typography", "color", "component library", "design system", "storybook", "accessibility", "wcag", "user experience"]),
    ("mobile",          ["mobile", "ios", "android", "swift", "kotlin", "react native", "flutter", "app store", "play store", "xcode"]),
    ("computer-science",["algorithms", "data structures", "leetcode", "competitive programming", "cs fundamentals", "operating systems", "networking", "computer science"]),
]

def infer_domains(text: str, max_domains: int = 3) -> list[str]:
    """Map free-text description to domain graph IDs."""
    text_lower = text.lower()
    scored = []
    for domain, keywords in DOMAIN_SIGNALS:
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scored.append((domain, score))
    scored.sort(key=lambda x: -x[1])
    # Always include algorithms as a secondary domain if not already top-3
    top = [d for d, _ in scored[:max_domains]]
    if "algorithms" not in top and len(top) < max_domains:
        top.append("algorithms")
    elif "algorithms" not in top:
        top[-1] = "algorithms"  # swap in at end
    return top if top else ["algorithms"]

def available_domains() -> list[str]:
    """List all pre-built domain graph IDs."""
    return [f.stem for f in GRAPHS_DIR.glob("*.json")]

def run_onboarding() -> list[str]:
    """
    Short 3-question interview. Returns list of inferred domain IDs.
    """
    print("\n🧠 skill-issue — quick setup\n")
    print("3 questions to personalise your knowledge graph.\n")

    answers = []

    # Q1 — what do you build
    print("1. What do you mainly build or work on?")
    print("   (e.g., web apps, ML models, mobile apps, design systems, DevOps infra, research...)")
    q1 = input("   › ").strip()
    answers.append(q1)

    # Q2 — tools / languages
    print("\n2. What languages or tools do you use most?")
    print("   (e.g., Python + PyTorch, TypeScript + React, Swift, Terraform, Figma...)")
    q2 = input("   › ").strip()
    answers.append(q2)

    # Q3 — one weak spot
    print("\n3. One concept in your field you know you're shaky on?")
    print("   (optional — helps us prioritise. Press Enter to skip.)")
    q3 = input("   › ").strip()
    if q3:
        answers.append(q3)

    combined = " ".join(answers)
    domains = infer_domains(combined)

    print(f"\n✓ Knowledge graphs initialised for: {', '.join(domains)}")
    print("  Add more anytime: skill-issue graph add-domain <name>")
    print(f"  See all available: skill-issue graph domains\n")

    return domains

def print_available_domains():
    """Print all available pre-built domain graphs."""
    domains = available_domains()
    print("\nAvailable pre-built knowledge graphs:\n")
    for d in sorted(domains):
        graph_path = GRAPHS_DIR / f"{d}.json"
        try:
            data = json.loads(graph_path.read_text())
            desc = data.get("description", "")
            node_count = len(data.get("nodes", []))
            print(f"  {d:<25} {node_count} concepts  —  {desc}")
        except Exception:
            print(f"  {d}")
    print()


if __name__ == "__main__":
    domains = run_onboarding()
    print(f"Domains: {domains}")
