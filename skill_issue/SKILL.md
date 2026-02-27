---
name: skill-issue
description: "Gamified active learning system that challenges the human during agentic coding sessions. Embeds spaced-retrieval challenges directly into the workflow at teaching moments. Tracks mastery via a pedagogical knowledge graph (fundamental concepts weighted by reuse frequency). Use whenever performing substantive coding, math, algorithm design, debugging, or architectural decisions — especially in research contexts (quantum computing, ML). Also trigger on: 'my stats', 'challenge me', 'show graph', or any direct reference to skill-issue."
allowed-tools: "Bash(skill-issue *)"
---

# skill-issue 🧠

**Core principle:** Challenges must be tied to what was just coded. Target high-reuse fundamentals the human hasn't mastered yet. Never random trivia.

## Setup (first run)

```bash
skill-issue init --domain quantum-ml   # or: algorithms, ml, python
```

Ask user's name + domain if not set. Greet returning users:
> "Welcome back, [name]. Streak: 🔥[N]. Level: [L]. Let's build."

## When to Challenge

**ALWAYS:** non-trivial algorithm, math derivation, subtle bug fix, domain-specific concept (parameter shift rule, attention, circuit identity)
**SOMETIMES** (per config): helper function with interesting logic, library/approach tradeoff
**NEVER:** boilerplate, imports, CI, crisis-debugging, focus mode, <8 min since last challenge, 3 consecutive skips

## Knowledge Graph — Check This First

Before issuing a challenge:
```bash
skill-issue graph weak --domain <domain> --json
```
If current code maps to a weak high-priority node → challenge on that concept.
After scoring: `skill-issue graph update --node <id> --score <0-3> --domain <domain>`

Priority = `reuse_weight × (1 - mastery)`. Fundamentals the human hasn't proven yet = highest priority.

## Challenge Format

```
🧠 SKILL CHECK #[N] — `[topic]` — Difficulty: [Level]

[1-2 sentences: what was just built/decided]

→ [The question]

`answer` `hint` `skip`
```

Types: `pen-paper` 📝 | `explain-back` 🗣️ | `predict` 🔮 | `spot-bug` 🐛 | `complexity` ⏱️ | `connect-dots` 🔗  
Vary types each session. Details → `references/challenge-design.md`

## Scoring

```
final_xp = round(base × difficulty_mult × streak_mult × hint_penalty)
```

| Score | Meaning | Base XP | Streak |
|---|---|---|---|
| 0 | Wrong/skip | 0 | reset |
| 1 | Partial | 5 | no change |
| 2 | Correct | 12 | +1 |
| 3 | Exceptional | 20 | +1 |

Difficulty: Apprentice 1×, Practitioner 1.5×, Expert 2×, Master 3×  
Streak bonus: `min(1.0 + streak×0.15, 2.5)` | Hint penalty: 0.75×

```bash
skill-issue score --id [N] --score [0-3] --topic [tag] --difficulty [Level]
```

Full formula + worked examples → `references/scoring-and-adaptation.md`

## Feedback Style

- Wrong → what they got right first, then the gap. Never shame.
- Partial → acknowledge + fill the gap
- Correct → brief confirmation + one extra insight
- Exceptional → "That's deeper than I was testing for."

## User Commands

| Say | Action |
|---|---|
| `my stats` / `trophy wall` | Show profile / leaderboard |
| `harder` / `easier` | Shift difficulty ±1 |
| `focus mode` / `challenges on` | Toggle off/on |
| `challenge me` | Force challenge now |
| `show graph` | `skill-issue graph show --domain <domain>` |
| `show brain` | `skill-issue graph web --domain <domain>` (D3 viz) |
| `hint` / `skip` | Hint (0.75× XP) / skip (score 0) |

## Session Lifecycle

**End of session:** `skill-issue report` → summary + update leaderboard  
**After 7+ days away:** start one difficulty level lower for first 2 challenges  
**3 consecutive wrong:** "Want me to walk through the last concept before we continue?"

## Visualization

```bash
skill-issue graph show --domain quantum-ml   # ASCII bar chart in terminal
skill-issue graph web --domain quantum-ml    # D3 force-directed graph in browser
```

Nodes sized by `reuse_weight`, colored by mastery. Click nodes to see challenge hooks.
