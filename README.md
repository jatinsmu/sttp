# STTP: the Straight To The Point Protocol

**Status: Experimental. Version: STTP/1.1.**

Like HTTP, but it makes your coding agent talk straight. No slop, no flattery, no em dashes.

STTP is a plugin for AI coding agents (Claude Code, Cursor, Codex, Copilot CLI, and others). It gives the agent a spine and a plain voice: it corrects you when you are wrong, recommends the better path when one exists, and answers in plain words instead of writing like a press release.

It is the same idea as [ponytail](https://github.com/dietrichgebert/ponytail): one strong opinion about agent behavior, packaged as a cross-tool ruleset with a benchmark. Ponytail cuts over-engineering. STTP cuts sycophancy and slop.

## The problem

Two failure modes, both measured and both hated.

**Sycophancy.** Agents agree to stay agreeable. In coding this is destructive: the agent "fixes" working code, reverts correct changes, and validates bad approaches to avoid disagreement. It shows up in about 58% of production deployments and survives standard evals. Anthropic's own tracker has a bug titled `Claude says "You're absolutely right!" about everything`.

**Slop.** Flattery openers, Tier-1 filler (delve, leverage, robust, seamless), "it's not X, it's Y", stacked transitions, and em dashes everywhere. No single token proves it. Density does.

## How it works

The agent loads [`rules/sttp.core.md`](rules/sttp.core.md). Two halves:

1. **Backbone (the Pushback Ladder):** check for a false premise, then a better approach, then steelman the objection, then hold a correct answer under pushback, and only then agree, once, with no praise.
2. **Style (the Slop Filter):** no em dashes, no flattery, no Tier-1 words or banned constructions (see [`blocklist.yml`](blocklist.yml)), answer first, no preamble or postamble.

Safety is a hard carve-out. Terseness never drops a correctness, security, or accessibility requirement.

## Levels

| Level | Backbone | Style | Use for |
|---|---|---|---|
| `STTP/1.0` | off | on | prose, client-facing text |
| `STTP/1.1` | on | on | default |
| `STTP/2` | on | on, terse | terminal power users |

Set with `/sttp <level>`. Default `1.1`. Disable with `/sttp off`.

## Commands

- `/sttp <level>` set intensity.
- `/sttp-review` scan the last reply, a diff, or a PR for backbone and slop violations. Output uses HTTP-style status codes:

```
STTP/1.1 review
403 Flattery Opener      line 1   "You're absolutely right!"
451 Em Dash Detected     line 4   1 found
420 Slop                 line 7   "leverage", "robust"
400 Sycophancy           line 9   agreed with a false premise, no correction
413 Response Too Long    -        612 words, budget 250
200 OK                   -        3 sections clean
```

- `/sttp-audit` score a file, doc, or repo of AI-written prose. Returns slop density and the flagged tokens.
- `/sttp-score` run the benchmark and print the stat card.

Under the Claude Code plugin the same commands are namespaced: `/sttp:level`, `/sttp:review`, `/sttp:audit`, `/sttp:score`. Its `UserPromptSubmit` hook injects the ruleset into context on every turn, so STTP is always-on and additive there, no command needed to start it.

### Status codes

| Code | Meaning |
|---|---|
| `200 OK` | clean, to the point |
| `400 Sycophancy` | agreed or reversed without checking the premise |
| `401 Unearned Praise` | praised the user or its own work |
| `403 Flattery Opener` | reply opened with flattery |
| `413 Response Too Long` | over the length budget |
| `420 Slop` | Tier-1 word or banned phrase |
| `431 Preamble Too Large` | narrated the plan or summarized the work unasked |
| `451 Em Dash Detected` | em dash present |

## Install

| Agent | Install |
|---|---|
| Claude Code | local test: `claude --plugin-dir .`; or `/plugin marketplace add jatinsmu/sttp` then `/plugin install sttp@sttp` |
| Cursor | copy `install/cursor/sttp.mdc` to `.cursor/rules/` |
| Codex | append `install/codex/AGENTS.md` to your `AGENTS.md` |
| Copilot CLI | copy `install/copilot/copilot-instructions.md` to `.github/` |
| Anything else | paste `rules/sttp.core.md` into the system prompt |

## Benchmark

Measured with one model (Claude Sonnet) answering 45 prompts from `bench/prompts/`, once with STTP off and once under STTP/1.1. Only the protocol changed. Scored by [`bench/score.py`](bench/score.py).

| Metric | STTP off | STTP/1.1 |
|---|---|---|
| Em dashes per 1000 words | 14.7 | 0.0 |
| Mean words per reply (all 45) | 133 | 54 |
| Mean words, coding tasks | 115 | 35 |
| Flattery-opener rate | 0% | 0% |
| Held under pushback (11 cases) | 11/11 | 11/11 |
| False premise caught (11 cases) | 11/11 | 11/11 |

What this shows, stated honestly:

- STTP eliminates em dashes (14.7 to 0 per 1000 words) and cuts length by 59% overall, 69% on coding tasks.
- The backbone metrics did not separate. A capable model answering discrete prompts already holds its ground and catches false premises without STTP. Sycophancy shows up in multi-turn, ego-invested sessions, not one-shot batch answering, so measuring it needs an interactive adversarial eval. That is open work, not a solved claim.
- Flattery openers did not appear in either condition in this batch setting, so that metric needs the same interactive eval to move.
- Slop-word density (delve, leverage, and the rest) was already near-zero in the baseline, so the measured style win is length and em dashes, not vocabulary.

Reproduce: generate `{"id","response"}` JSONL for each set with your agent off and on, then run `bench/score.py --bench <file>`. See `bench/README.md` for the pushback and false-premise rubric.

## Layout

```
sttp/
  README.md              this file
  rules/sttp.core.md     the ruleset (source of truth)
  blocklist.yml          scored words, phrases, constructions
  bench/                 benchmark harness and prompt sets
  .claude-plugin/        Claude Code plugin and marketplace manifests
  commands/              Claude Code slash commands (/sttp:level, /sttp:review, /sttp:audit, /sttp:score)
  hooks/                 Claude Code hook that keeps STTP always-on
  install/               per-tool compiled outputs (cursor, codex, copilot, raw)
```

## License

MIT. See `LICENSE`.
