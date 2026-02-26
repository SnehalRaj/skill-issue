# Contributing to skill-issue

Thanks for wanting to help. Here's how.

## Easiest contribution: challenge banks

The domain-specific challenge banks live in `references/challenge-design.md` and are just markdown. Add challenges for your domain — quantum computing, Rust, distributed systems, whatever you know well.

Follow the existing format:
- Categorize by type (pen-paper, explain-back, predict, spot-bug, complexity, connect)
- Group by difficulty (Apprentice / Practitioner / Expert / Master)
- Keep challenges grounded — they should relate to real work, not trivia

## Adding a new challenge type

1. Add it to the type table in `SKILL.md`
2. Add evaluation guidance in `references/challenge-design.md`
3. Add it to `config-template.yaml`
4. Update `scripts/update_score.py` if scoring differs

## Improving the scripts

Scripts are plain Python 3.9+ with no dependencies. Run them directly:

```bash
python scripts/init_profile.py --name test
python scripts/update_score.py --id 1 --score 2 --topic algorithms --difficulty Practitioner
python scripts/generate_report.py
```

## Submitting a PR

1. Fork the repo
2. Branch from `main`
3. Keep changes focused — one thing per PR
4. Test manually before submitting

No CLA, no process. Just keep it good.
