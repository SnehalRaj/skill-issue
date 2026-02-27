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

## The problem nobody's talking about

There's a study you should know about.

METR ran a randomized controlled trial in early 2025 — experienced open-source developers, working on their own codebases, real issues. With AI tools, they took **19% longer** to complete tasks than without. But here's the unsettling part: those same developers *believed* AI had made them 20% faster. Even after experiencing the slowdown firsthand, the belief held.

Anthropic's own research found something similar: AI-assisted coding significantly lowers codebase comprehension. Developers who rely more on AI perform worse at debugging, conceptual understanding, and code reading. "Just reviewing the generated code" gives you, at best, a flimsy grasp of what you're shipping.

Trust in AI coding tools is [already falling](https://leaddev.com/technical-direction/trust-in-ai-coding-tools-is-plummeting) — 33% of developers trusted AI output accuracy in 2025, down from 43% the year before.

This isn't an argument against AI tools. It's a description of a gap that's opening up quietly, without anyone noticing.

---

## The gym analogy

Everyone goes to the gym. Not because physical labor disappeared — it mostly has — but because staying physically capable requires deliberate effort. You have to maintain it. The infrastructure for that is everywhere: gyms, workout plans, progress tracking, coaches.

Coding used to be that workout for your brain. Every bug you debugged, every algorithm you reasoned through, every system you designed from scratch was building something. Judgment. Pattern recognition. The ability to hold complexity in your head and work through it.

AI agents are changing that. Not by making you worse — but by removing the friction that was doing the work. The code appears. It looks right. You move on. And slowly, without noticing, you stop reasoning from first principles.

There's no gym for this yet.

---

## What skill-issue does

When your agent builds something non-trivial, it fires a challenge grounded in what just happened. Not trivia. Not a random LeetCode problem. Something directly tied to the code you just shipped.

You answer it. It scores you 0–3. Your knowledge graph updates.

Over time, it shows you exactly where your understanding is solid and where it's quietly fading. The mastery score decays if you don't practice — because real understanding works the same way.

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

Each domain has a curated graph of concepts weighted by how often they come up in real work. High-weight concepts you haven't proven → top priority.

Mastery fades over time (3-day grace, then 0.02/day). Use it or lose it.

---

## Install

### Claude Code

Two separate commands (don't combine them):

```
/plugin marketplace add SnehalRaj/skill-issue-marketplace
```

```
/plugin install skill-issue@skill-issue-marketplace
```

Open a new session.

### pip (Cursor, Codex, any agent)

```bash
pip install skill-issue-cc
skill-issue init
```

Paste the output of `skill-issue init --print` into your editor's system prompt.

---

## Onboarding

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

Three questions, plain English. It figures out which domains to load.

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

Challenges are grounded in what was just built. Not random trivia.

---

## Commands

| Command | What it does |
|---|---|
| `skill-issue init` | Onboarding + profile setup |
| `skill-issue stats` | XP, level, streak, topic breakdown |
| `skill-issue graph show --domain <d>` | ASCII viz |
| `skill-issue graph weak --domain <d>` | Top priority nodes |
| `skill-issue graph web --domain <d>` | D3 force graph in browser |
| `skill-issue graph domains` | List available domains |
| `skill-issue graph update --node <n> --score <0-3> --domain <d>` | Update mastery |
| `skill-issue report` | Regenerate trophy wall |
| `skill-issue export --format json` | Export history |

**Voice commands** (say to your agent):

| Say | Does |
|---|---|
| `my stats` / `trophy wall` | Show profile |
| `show graph` / `show brain` | Visualize knowledge |
| `challenge me` | Force a challenge |
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

Add your own in `references/knowledge_graphs/`.

---

## Progression

```
XP = base × difficulty × streak_multiplier
```

| Score | Meaning | Base XP |
|---|---|---|
| 0 | Wrong / Skipped | 0 |
| 1 | Partial | 5 |
| 2 | Correct | 12 |
| 3 | Exceptional | 20 |

Difficulty multipliers: Apprentice 1× → Practitioner 1.5× → Expert 2× → Master 3×

Streak bonus tops out at 2.5× for consecutive correct answers.

---

## Persistent State

Everything's in `~/.skill-issue/`. Plain JSON/YAML, no database.

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

The name's a joke. Claude has skills (literally, `.skill` files). What about yours?

The METR study found that developers *felt* faster with AI even when they were measurably slower. That perception gap is the real problem — you can't fix what you can't see. skill-issue makes the invisible visible: where your understanding is solid, where it's drifting, and what to work on next.

A developer who actually understands the code they ship is more effective, more resilient, and harder to replace. One well-timed challenge beats an hour of passive tutorials. Your trophy wall tracks real growth — no leaderboard against others, just you versus yesterday's you.

---

## Contributing

Knowledge graphs are JSON in `references/knowledge_graphs/`. Scripts are plain Python, zero dependencies.

See [CONTRIBUTING.md](CONTRIBUTING.md) or open an issue.

**MIT License**

---

<div align="center">
  <sub>Works with Claude Code · Cursor · Codex · OpenCode · any agent that reads a system prompt</sub>
</div>
