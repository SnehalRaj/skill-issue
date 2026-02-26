# skill-issue 🧠

> *You're not bad at coding. You just have a skill issue.*

A gamified active learning system that turns passive AI-assisted coding into genuine skill building. Works with Claude Code, Cursor, Copilot, and any agentic coding workflow.

---

## The Problem

Modern AI coding tools create a dangerous pattern: **cognitive offloading without cognitive engagement**. You accept generated code, ship it, and slowly forget how to derive, debug, and reason from first principles.

**skill-issue** fixes this. It embeds spaced-repetition challenges directly into your coding workflow — pen-and-paper calculations, explain-it-back prompts, predict-the-output puzzles, spot-the-bug drills — at exactly the moment you need them.

---

## How It Works

The agent tracks what it just built and challenges you on it:

```
🧠 SKILL CHECK #47 — `quantum-circuits` — Difficulty: Expert

I just used the parameter shift rule to compute the gradient of an expectation value.

→ In 2-3 sentences: Why is the shift exactly π/2? What property of the gate
  generator makes this work?

`[answer]` `[hint]` `[skip]`
```

You answer. The agent evaluates, gives feedback, and awards XP. Then coding resumes.

---

## Features

- **6 challenge types**: Pen & Paper 📝, Explain Back 🗣️, Predict 🔮, Spot the Bug 🐛, Complexity ⏱️, Connect the Dots 🔗
- **Persistent progress**: XP, streaks, per-topic mastery levels (Apprentice → Practitioner → Expert → Master)
- **Difficulty adaptation**: Auto-adjusts based on your rolling performance window
- **Streak multipliers**: Up to 2.5× XP bonus for consecutive correct answers
- **Trophy wall**: Human-readable `leaderboard.md` that updates after every session
- **Smart triggering**: Challenges fire on teaching moments, never on boilerplate — respects cooldowns and focus mode
- **Full command set**: `harder`, `easier`, `focus mode`, `my stats`, `challenge me`, `trophy wall`

---

## Installation

```bash
# Clone the skill
git clone https://github.com/SnehalRaj/skill-issue

# Initialize your profile (first run)
python skill-issue/scripts/init_profile.py your-name
```

Then load `SKILL.md` into your Claude Code / Cursor / agent context. The agent handles the rest.

---

## XP Formula

```
final_xp = round(base_xp × difficulty_mult × streak_mult × hint_penalty)
```

| Score | Meaning | Base XP |
|---|---|---|
| 0 | Wrong / Skipped | 0 |
| 1 | Partial | 5 |
| 2 | Correct | 12 |
| 3 | Exceptional | 20 |

Difficulty multipliers: Apprentice 1×, Practitioner 1.5×, Expert 2×, Master 3×

Streak multiplier: `min(1.0 + streak × 0.15, 2.5)` — caps at 2.5×

---

## Project Structure

```
skill-issue/
├── SKILL.md                        # Main skill (load this into your agent)
├── references/
│   ├── challenge-design.md         # Challenge types, domain banks, difficulty tiers
│   ├── scoring-and-adaptation.md   # Full XP math, topic mastery, profile schemas
│   └── interaction-patterns.md     # UX patterns, feedback templates, leaderboard format
├── scripts/
│   ├── init_profile.py             # Bootstrap ~/.skill-issue/
│   ├── update_score.py             # Apply XP after a challenge
│   ├── generate_report.py          # Regenerate trophy wall
│   └── export_stats.py             # Export history to JSON/CSV
└── assets/
    └── config-template.yaml        # Annotated default config
```

---

## Domain Banks

Built-in challenge banks for:
- ⚛️ **Quantum computing** — circuits, RBS gates, VQE, classical shadows, barren plateaus
- 🤖 **Machine learning** — backprop, attention, loss functions, regularization
- 📐 **Linear algebra** — eigenvalues, tensor products, unitary proofs
- ⚙️ **Algorithms** — complexity analysis, correctness arguments, recurrences
- 🐍 **Python / software engineering** — mutability, broadcasting, decorators

Extend with your own domains in `references/challenge-design.md`.

---

## Commands

| Say this | Does this |
|---|---|
| `my stats` | Show XP, level, streak |
| `trophy wall` | Show full leaderboard |
| `harder` / `easier` | Shift difficulty bias |
| `focus mode` | Pause all challenges |
| `challenge me` | Force a challenge now |
| `hint` | Get a nudge (0.75× XP penalty) |
| `skip` | Skip (streak resets) |

---

## Philosophy

The name is a playful inversion of the gaming meme. Claude has skills (literally, `.skill` files). But what about *your* skills?

**skill-issue** is built on three beliefs:

1. **Understanding compounds.** A researcher who deeply understands the code they ship is 10× more effective than one who accepts and moves on.
2. **Interruption is a feature.** The right challenge at the right moment is worth more than a passive tutorial at the wrong one.
3. **Personal, not competitive.** Your trophy wall tracks your growth — not a leaderboard against others. No gamification dark patterns.

---

## Contributing

Pull requests welcome. Areas that would most benefit:
- More domain-specific challenge banks (add to `references/challenge-design.md`)
- Additional challenge types
- Better difficulty calibration data
- Integration guides for specific coding agents

---

## License

MIT

---

*Built by [@SnehalRaj](https://github.com/SnehalRaj) with Claude Code*
