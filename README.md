<div align="center">

<img src="assets/demo/skill-issue-demo.gif" width="600" alt="skill-issue demo" />

<h1>skill-issue 🧠</h1>

<p><strong>Gamified active learning, embedded in your AI coding workflow.</strong></p>

<p>
  <a href="https://pypi.org/project/skill-issue-cc/"><img src="https://img.shields.io/pypi/v/skill-issue-cc?color=blue&label=pip" alt="PyPI" /></a>
  <a href="https://github.com/SnehalRaj/skill-issue/blob/main/LICENSE"><img src="https://img.shields.io/github/license/SnehalRaj/skill-issue?color=green" alt="License" /></a>
  <a href="https://github.com/SnehalRaj/skill-issue/stargazers"><img src="https://img.shields.io/github/stars/SnehalRaj/skill-issue?style=flat" alt="Stars" /></a>
  <img src="https://img.shields.io/badge/works%20with-Claude%20Code-orange" alt="Claude Code" />
  <img src="https://img.shields.io/badge/works%20with-Cursor-purple" alt="Cursor" />
</p>

<p><em>Your AI writes the code. But do <strong>you</strong> actually understand it?</em></p>

</div>

---

## The Problem

AI coding tools are making it easy to ship code you don't fully understand.

Not because you're lazy — because the workflow doesn't give you a reason to engage. The code looks right, you move on. Over time, you stop deriving. Stop reasoning from first principles. The skills atrophy quietly.

**skill-issue** is the antidote. It watches what your agent builds and challenges you on it — at the exact moment you'd otherwise just accept and continue.

---

## How It Works

The agent codes as normal. When it does something non-trivial, it pauses:

```
🧠 SKILL CHECK #23 — `algorithms` — Difficulty: Practitioner

I just added memoization to fix the slow recursion.

→ What was the time complexity before caching? And after? Explain why.

`[answer]`  `[hint]`  `[skip]`
```

You answer. It evaluates, gives feedback, awards XP. Then coding resumes.

**It never interrupts boilerplate.** Only teaching moments.

---

## Install

### Claude Code (native)

```
/plugin marketplace add SnehalRaj/skill-issue-marketplace
/plugin install skill-issue@skill-issue-marketplace
```

Open a session. Done.

### Cursor

```
/plugin-add skill-issue
```

### Codex / Everything Else

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

**Difficulty multipliers:** 1× → 1.5× → 2× → 3× (Apprentice through Master)

**Streak bonus:** up to **2.5×** for consecutive correct answers

**Per-topic mastery:** each topic levels up independently based on your rolling accuracy.

```
Apprentice → Practitioner → Expert → Master
```

---

## Commands

Say these to your agent at any time:

| Command | Effect |
|---|---|
| `my stats` | XP, level, streak, topic breakdown |
| `trophy wall` | Full leaderboard with progress bars |
| `challenge me` | Force a challenge right now |
| `harder` / `easier` | Shift difficulty up or down |
| `focus mode` | Pause all challenges |
| `hint` | Get a nudge (0.75× XP) |
| `skip` | Skip — streak resets |

---

## Persistent State

Everything lives in `~/.skill-issue/` — plain JSON/YAML, no database.

```
~/.skill-issue/
├── profile.json        # XP, streak, topic levels, milestones
├── config.yaml         # frequency, domains, difficulty bias
├── leaderboard.md      # your trophy wall
└── sessions/           # per-session challenge logs
    └── 2026-02-27.json
```

Version-controllable. Portable. Human-readable.

---

## CLI Reference

```bash
skill-issue stats          # current profile summary
skill-issue report         # regenerate trophy wall
skill-issue export --format csv    # export history
skill-issue export --format json
```

---

## Domains

Built-in challenge banks for:

- **Algorithms & Data Structures** — complexity, correctness, tradeoffs
- **Debugging** — spot the bug, trace the failure, fix it right
- **System Design** — tradeoffs, scalability, architecture decisions
- **ML / AI** — gradients, loss functions, architecture choices
- **Python** — mutability, broadcasting, decorators, concurrency

Extend with your own in `references/challenge-design.md`.

---

## Philosophy

> *The name is a playful inversion. Claude has skills (literally, `.skill` files). But what about your skills?*

Three beliefs underpin this:

1. **Understanding compounds.** A developer who deeply understands the code they ship is 10× more effective long-term.
2. **Interruption at the right moment.** One well-timed challenge beats a passive tutorial.
3. **Personal, not competitive.** Your trophy wall tracks your own growth — no leaderboard against others.

---

## Contributing

The challenge banks (`references/challenge-design.md`) are just markdown — easy to extend for your domain. Scripts are plain Python with no dependencies.

See [CONTRIBUTING.md](CONTRIBUTING.md) or open an issue.

**MIT License**

---

<div align="center">
  <sub>Works with Claude Code · Cursor · Codex · OpenCode · any agent that reads a system prompt</sub>
</div>
