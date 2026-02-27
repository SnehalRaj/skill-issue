# Scoring & Adaptation System

## XP Formula

```
final_xp = round(base_xp × difficulty_mult × streak_mult × hint_penalty)
```

### Base XP by Score
| Score | Meaning | Base XP |
|---|---|---|
| 0 | Wrong / Skipped | 0 |
| 1 | Partial credit | 5 |
| 2 | Correct | 12 |
| 3 | Exceptional | 20 |

### Difficulty Multipliers
| Difficulty | Multiplier |
|---|---|
| Apprentice | 1.0× |
| Practitioner | 1.5× |
| Expert | 2.0× |
| Master | 3.0× |

### Streak Multiplier
```
streak_mult = min(1.0 + current_streak × 0.15, 2.5)
```
| Streak | Multiplier |
|---|---|
| 0 | 1.00× |
| 1 | 1.15× |
| 3 | 1.45× |
| 5 | 1.75× |
| 7 | 2.05× |
| 10+ | 2.50× (cap) |

### Hint Penalty
- No hint: 1.0×
- Hint used: 0.75×

### Worked Examples
```
Expert, score 2, streak 5, no hint:
  12 × 2.0 × 1.75 × 1.0 = 42 XP

Master, score 3, streak 10, no hint:
  20 × 3.0 × 2.5 × 1.0 = 150 XP

Practitioner, score 2, streak 0, hint used:
  12 × 1.5 × 1.0 × 0.75 = 13.5 → 14 XP
```

---

## Topic Level Calculation

Rolling window of last 20 attempts per topic:
```
accuracy = sum(score >= 2 for s in last_20) / len(last_20)

Master:       accuracy >= 0.90 AND total_attempts >= 15
Expert:       accuracy >= 0.75 AND total_attempts >= 10
Practitioner: accuracy >= 0.55 AND total_attempts >= 5
Apprentice:   everything else
```

---

## Overall Level

Based on total XP:
```
xp >= 5000 → Master
xp >= 2000 → Expert
xp >= 500  → Practitioner
else       → Apprentice
```

---

## Difficulty Selection Algorithm

```python
def select_difficulty(current_level, bias=0):
    levels = ["Apprentice", "Practitioner", "Expert", "Master"]
    idx = levels.index(current_level)
    # 60% current, 30% stretch, 10% comfort
    weights = {
        idx: 0.60,
        min(idx + 1, 3): 0.30,   # stretch
        max(idx - 1, 0): 0.10,   # comfort
    }
    effective_idx = max(0, min(3, idx + bias))
    # ... random.choices with weights
```

If human says "harder" / "easier": shift `difficulty.bias` in config.yaml by ±1 (range: -2 to +2).

---

## Milestone Definitions

| Milestone | Trigger | Message |
|---|---|---|
| `first_challenge` | Complete first challenge | "First challenge completed! The journey begins. 🎯" |
| `streak_5` | Hit 5-streak | "5 in a row! You're in the zone. 🔥🔥" |
| `streak_10` | Hit 10-streak | "10-streak! Absolutely locked in. 🔥🔥🔥" |
| `streak_20` | Hit 20-streak | "20-STREAK. Legendary. 🔥🔥🔥🔥" |
| `topic_expert` | Any topic → Expert | "[topic] Expert unlocked! 🔷" |
| `topic_master` | Any topic → Master | "[topic] MASTERED. ⭐" |
| `xp_500` | Reach 500 XP | "500 XP! Leveling up. 💎" |
| `xp_2000` | Reach 2000 XP | "2000 XP! Expert level. 💎💎" |
| `xp_5000` | Reach 5000 XP | "5000 XP! Master level. You've earned it. 💎💎💎" |
| `all_types` | Used all 6 challenge types | "Full spectrum learner — completed every challenge type! 🌈" |
| `comeback` | 3+ correct after 3+ wrong streak | "Comeback! 💪" |

---

## Profile Schema (profile.json v2)

```json
{
  "version": 2,
  "username": "snehal",
  "created_at": "2026-02-25T10:00:00Z",
  "overall_level": "Practitioner",
  "total_xp": 847,
  "total_challenges": 142,
  "scores": {"0": 15, "1": 29, "2": 82, "3": 16},
  "current_streak": 4,
  "best_streak": 12,
  "topics": {
    "quantum-circuits": {
      "attempts": 45,
      "scores": [2, 3, 2, 1, 2, ...],
      "level": "Expert",
      "last_challenged": "2026-02-25T14:20:00Z"
    }
  },
  "preferences": {
    "challenge_frequency": "normal",
    "difficulty_bias": 0,
    "focus_mode": false,
    "enabled_types": ["pen-paper", "explain-back", "predict", "spot-bug", "complexity", "connect-dots"]
  },
  "milestones": [
    {"type": "first_challenge", "date": "..."},
    {"type": "streak_10", "date": "..."},
    {"type": "topic_master", "topic": "linear-algebra", "date": "..."}
  ],
  "next_challenge_id": 143
}
```

## Session Log Schema (sessions/YYYY-MM-DD_NNN.json)

```json
{
  "session_id": "2026-02-25_001",
  "started_at": "2026-02-25T10:00:00Z",
  "ended_at": "2026-02-25T14:30:00Z",
  "challenges": [
    {
      "id": 138,
      "timestamp": "2026-02-25T10:22:00Z",
      "type": "pen-paper",
      "topic": "quantum-circuits",
      "difficulty": "Expert",
      "question": "...",
      "human_answer": "0.5",
      "correct_answer": "0.5",
      "score": 2,
      "xp_earned": 24,
      "hint_used": false,
      "feedback_given": "...",
      "context": "Working on QGNN implementation"
    }
  ],
  "summary": {
    "total_challenges": 6,
    "scores": {"0": 0, "1": 1, "2": 4, "3": 1},
    "xp_earned": 112,
    "topics_covered": ["quantum-circuits", "linear-algebra"],
    "streak_at_end": 4
  }
}
```
