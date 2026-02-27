<div align="center">

<img src="assets/demo/skill-issue-demo.gif" width="600" alt="skill-issue demo" />

<h1>skill-issue</h1>

<p>
  <a href="https://pypi.org/project/skill-issue-cc/"><img src="https://img.shields.io/pypi/v/skill-issue-cc?color=blue&label=pip" alt="PyPI" /></a>
  <a href="https://github.com/SnehalRaj/skill-issue/blob/main/LICENSE"><img src="https://img.shields.io/github/license/SnehalRaj/skill-issue?color=green" alt="License" /></a>
  <a href="https://github.com/SnehalRaj/skill-issue/stargazers"><img src="https://img.shields.io/github/stars/SnehalRaj/skill-issue?style=flat" alt="Stars" /></a>
  <img src="https://img.shields.io/badge/works%20with-Claude%20Code-orange" alt="Claude Code" />
  <img src="https://img.shields.io/badge/works%20with-Cursor-purple" alt="Cursor" />
</p>

<p><strong>Your AI writes the code. But does your brain keep up?</strong></p>

</div>

---

## The Problem

AI coding tools let you ship code you don't understand. Not because you're lazy—because there's no friction. The code looks right, you move on, and slowly you stop reasoning from first principles.

**skill-issue** is a living pedagogical brain alongside your AI agent. It tracks which fundamental concepts you've actually mastered, challenges you at teaching moments, and makes sure your understanding grows with your codebase.

---

## How It Works

```
You code → Agent builds something non-trivial → Challenge fires
    ↓
You answer → Score (0-3) → Knowledge graph updates
    ↓
Next challenge targets your weakest high-value concepts
```

The system prioritizes challenges on concepts that are both **fundamental** (high reuse_weight) and **unmastered** (low mastery). You stop getting quizzed on what you already know.

---

## Knowledge Graph

The hero feature. Each domain has a curated graph of fundamental concepts, weighted by how often they appear in real work.

```
skill-issue graph show --domain machine-learning

Knowledge Graph: machine-learning
============================================================

[GOOD]     gradient-descent       [####..........................] 0.42  (2)
[WEAK]     bias-variance-tradeoff [##............................] 0.09  (1)
[GOOD]     backpropagation        [#############.................] 0.45  (2)
[WEAK]     regularization         [..............................] 0.00
[WEAK]     cross-validation       [..............................] 0.00
[WEAK]     loss-functions         [######........................] 0.21  (1)
[WEAK]     attention-mechanism    [..............................] 0.00

Priority Queue (work on these next):
  >> regularization      (priority: 0.95 = weight:0.95 x gap:1.00)
  >> cross-validation    (priority: 0.95 = weight:0.95 x gap:1.00)
  >> attention-mechanism (priority: 0.95 = weight:0.95 x gap:1.00)

Total nodes: 12 | Avg mastery: 0.10 | 0 mastered | 10 weak
```

**How it works:**
- **reuse_weight** (0.0–1.0): How fundamental this concept is. Higher = appears everywhere.
- **mastery** (0.0–1.0): Your proven understanding, updated with EMA after each challenge.
- **priority** = `reuse_weight × (1 - mastery)`. High-weight concepts you haven't proven yet = highest priority.
- **Gentle decay**: Mastery slowly fades if you don't practice (3-day grace period, then 0.02/day).

---

## Onboarding

A 3-question interview that auto-infers your domains from plain English:

```
skill-issue init

3 questions to personalise your knowledge graph.

1. What do you mainly build or work on?
   > I train ML models and do some backend API work

2. What languages or tools do you use most?
   > Python, PyTorch, FastAPI, PostgreSQL

3. One concept you know you are shaky on? (optional)
   > always forget when cross-validation goes wrong

Knowledge graphs initialised for: machine-learning, backend-systems, algorithms
```

---

## Install

**Claude Code (native plugin):**
```bash
/plugin marketplace add SnehalRaj/skill-issue-marketplace
/plugin install skill-issue@skill-issue-marketplace
```

**Cursor:**
```bash
/plugin-add skill-issue
```

**pip (works everywhere):**
```bash
pip install skill-issue-cc
skill-issue init
```

---

## Challenge Types

| | Type | What it tests |
|---|---|---|
| 📝 | **Pen & Paper** | Can you compute this by hand? |
| 🗣️ | **Explain Back** | Can you explain *why* this works? |
| 🔮 | **Predict** | What does this function return? |
| 🐛 | **Spot the Bug** | Here's a broken version — find it |
| ⏱️ | **Complexity** | What's the Big-O? Can it be better? |
| 🔗 | **Connect** | How does this relate to X? |

Challenges are always grounded in what was just built — never random trivia.

---

## Commands

| Command | Effect |
|---|---|
| `skill-issue init` | Onboarding interview + profile setup |
| `skill-issue stats` | XP, level, streak, topic breakdown |
| `skill-issue graph show --domain <d>` | ASCII visualization of knowledge graph |
| `skill-issue graph weak --domain <d>` | Top priority nodes to study |
| `skill-issue graph web --domain <d>` | D3 force-directed graph in browser |
| `skill-issue graph domains` | List all available domains |
| `skill-issue graph update --node <n> --score <0-3> --domain <d>` | Update mastery after a challenge |
| `skill-issue report` | Regenerate trophy wall |
| `skill-issue export --format json` | Export history |

**In-session voice commands** (say to your agent):

| Say | Action |
|---|---|
| `my stats` / `trophy wall` | Show profile / leaderboard |
| `show graph` / `show brain` | Visualize knowledge graph |
| `challenge me` | Force a challenge now |
| `harder` / `easier` | Shift difficulty ±1 |
| `focus mode` | Pause challenges |
| `hint` / `skip` | Hint (0.75× XP) / skip |

---

## Domains

| Domain | Nodes | Covers |
|---|---|---|
| `machine-learning` | 12 | Gradient descent, backprop, transformers, bias-variance |
| `computer-science` | 12 | Complexity, DP, trees/graphs, concurrency, OS |
| `algorithms` | 8 | Sorting, binary search, DP, graph traversal |
| `quantum-ml` | 14 | Variational circuits, parameter shift, barren plateaus |
| `web-frontend` | 10 | Event loop, closures, promises, DOM, CSS |
| `backend-systems` | 10 | Indexing, ACID, caching, distributed systems |
| `devops` | 8 | Containers, Kubernetes, CI/CD, IaC, GitOps |
| `design-systems` | 8 | Visual hierarchy, design tokens, typography, WCAG |
| `mobile` | 8 | App lifecycle, state, navigation, offline-first |

Add your own graphs in `references/knowledge_graphs/`.

---

## Progression System

```
XP = base × difficulty × streak_multiplier
```

| Score | Meaning | Base XP |
|---|---|---|
| 0 | Wrong / Skipped | 0 |
| 1 | Partial | 5 |
| 2 | Correct | 12 |
| 3 | Exceptional | 20 |

**Difficulty multipliers:** Apprentice 1× → Practitioner 1.5× → Expert 2× → Master 3×

**Streak bonus:** up to 2.5× for consecutive correct answers

**Mastery update:** EMA with α=0.3 (recent performance weighted, history preserved)

---

## Persistent State

Everything lives in `~/.skill-issue/` — plain JSON/YAML, no database.

```
~/.skill-issue/
├── profile.json           # XP, streak, topic levels, milestones
├── config.yaml            # frequency, domains, difficulty bias
├── knowledge_state.json   # per-node mastery for all domains
├── leaderboard.md         # your trophy wall
└── sessions/              # per-session challenge logs
    └── 2026-02-27.json
```

Version-controllable. Portable. Human-readable.

---

## Philosophy

> *The name is a playful inversion. Claude has skills (literally, `.skill` files). But what about your skills?*

Three beliefs underpin this:

1. **Understanding compounds.** A developer who deeply understands the code they ship is 10× more effective long-term.
2. **Interruption at the right moment.** One well-timed challenge beats a passive tutorial.
3. **Personal, not competitive.** Your trophy wall tracks your own growth — no leaderboard against others.

---

## Contributing

The knowledge graphs (`references/knowledge_graphs/`) are JSON — easy to add new domains or concepts. Scripts are plain Python with zero dependencies.

See [CONTRIBUTING.md](CONTRIBUTING.md) or open an issue.

**MIT License**

---

<div align="center">
  <sub>Works with Claude Code · Cursor · Codex · OpenCode · any agent that reads a system prompt</sub>
</div>
