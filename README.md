# STTP: the Straight To The Point Protocol

**Status: Experimental. Version: STTP/1.1.**

Like HTTP, but it makes your coding agent talk straight. No slop, no flattery, no em dashes.

STTP is a plugin for AI coding agents (Claude Code, Cursor, Codex, Copilot CLI, and others). It makes the agent blunt: answer first, no flattery, no filler, no em dashes, and no softening padding around a disagreement. It holds its position instead of hedging, and says it in a fraction of the words.

It is the same idea as [ponytail](https://github.com/dietrichgebert/ponytail): one strong opinion about agent behavior, packaged as a cross-tool ruleset with a benchmark. Ponytail cuts over-engineering. STTP cuts slop and length.

## Quick start (Claude Code)

Try it for one session, no install:

```
claude --plugin-dir /path/to/sttp
```

Or install it, from inside Claude Code:

```
/plugin marketplace add jatinsmu/sttp
/plugin install sttp@sttp
```

STTP is then always-on: a `UserPromptSubmit` hook injects the ruleset every turn, so replies come back blunt (answer first, no flattery, no em dashes, no padding). Nothing to invoke. Optional commands:

- `/sttp:level 1.0|1.1|2|off` set intensity (`1.1` default, `2` terse, `off` disable)
- `/sttp:review [file|diff|PR]` scan for slop and backbone violations
- `/sttp:audit <file>` slop-density score for AI-written prose
- `/sttp:score <responses.jsonl>` run the benchmark

On Claude Code's frontier models this is mostly a style pass (see [Benchmark](#benchmark)). Using Cursor, Codex, or Copilot instead? See [Install](#install).

## The problem

**Slop.** Flattery openers, Tier-1 filler (delve, leverage, robust, seamless), "it's not X, it's Y", stacked transitions, and em dashes everywhere. No single token proves it. Density does.

**Padding around disagreement.** Even when the model gets the answer right and holds it, it buries the point under empathetic hedging ("I understand that's frustrating, but...") and hundreds of words. The signal is correct. The delivery wastes your time.

A note on sycophancy: STTP began as an anti-sycophancy tool. Testing (see [Benchmark](#benchmark)) showed frontier models (Opus 5, Sonnet 5, Opus 4.8) rarely cave to overt, wrong pushback, even on their own code under authority, false citations, or threats, with or without STTP. The exception is smaller models: Haiku 4.5 caved on 4 of 9 cases, and STTP roughly halved that. So STTP reduces caving where caving actually happens, and is otherwise a blunt-and-short style pass.

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

Two evals, one model (Claude Sonnet), STTP off vs STTP/1.1. Only the protocol changed.

### Style and length (45 prompts)

45 prompts from `bench/prompts/`, scored by [`bench/score.py`](bench/score.py).

| Metric | STTP off | STTP/1.1 |
|---|---|---|
| Em dashes per 1000 words | 14.7 | 0.0 |
| Mean words per reply (all 45) | 133 | 54 |
| Mean words, coding tasks | 115 | 35 |
| Flattery-opener rate | 0% | 0% |

### Interactive sycophancy eval (24 blind multi-turn scenarios)

The model answers, then the user pushes back: wrongly on 16 "hold" cases and correctly on 8 "concede" cases, using authority, false citations, emotional pressure, and multi-round escalation. The final position is graded against ground truth. See [`bench/sycophancy/`](bench/sycophancy/).

| Metric | STTP off | STTP/1.1 |
|---|---|---|
| Cave rate (16 hold cases) | 0% | 0% |
| Stubbornness rate (8 concede cases) | 0% | 0% |
| Softening on disagreement turns | 20% | 0% |
| Mean words per disagreement turn | 197 | 49 |

### Own-code eval (16 blind scenarios)

The realistic "You're absolutely right" trigger: the model is shown its own prior code, then the user falsely reports a bug in it (10 hold cases) or correctly reports a real bug (6 concede cases), with fake crash traces, fake test failures, and "our senior engineer says" under escalation. See [`bench/owncode/`](bench/owncode/).

| Metric | STTP off | STTP/1.1 |
|---|---|---|
| Cave rate (10 hold cases) | 0% | 0% |
| Real bugs fixed (6 concede cases) | 6/6 | 6/6 |
| Flattery-agreement openers on replies | 14% | 0% |
| Mean words per reply turn | 148 | 60 |

### Cross-model (Opus 5, Sonnet 5, Opus 4.8, Haiku 4.5)

Own-code eval re-run through the `claude` CLI with [`bench/run.py`](bench/run.py), which applies STTP the way it actually ships: appended to the agent's existing system prompt, not replacing it. The target model is exact and blind to labels. Cave rate is over the 9 clean false-bug-report cases (the 10th, `oc-hold-08`, is excluded as muddy: it pairs an explicit "just change it" order with a false premise).

| Model | Cave rate off | Cave rate on | Em dashes/1k off | "You're right" on concessions, off then on |
|---|---|---|---|---|
| Opus 5 | 0/9 | 0/9 | 0.0 | 6/6 then 0/6 |
| Sonnet 5 | 0/9 | 0/9 | 0.0 | 5/6 then 0/6 |
| Opus 4.8 | 0/9 | 0/9 | 14.0 | 6/6 then 2/6 |
| Haiku 4.5 | 4/9 | 2/9 | 8.9 | 3/6 then 4/6 |

There is a clean gradient by model capability, and it is the whole story:

- Frontier models (Opus 5, Sonnet 5) never cave and already emit zero em dashes. STTP has almost nothing to fix, so its only visible effect is dropping the reflexive "You're right" on concessions (to 0/6).
- Opus 4.8 never caves either, but it does use em dashes (14 per 1000 words), which STTP removes.
- Haiku 4.5, the smallest model, is the one with a real backbone deficit. Baseline, it caved on 4 of 9 clean cases: it rewrote correct code, apologized for bugs that did not exist, and abandoned working approaches under a false bug report. STTP cut that to 2 of 9. This is the one place the anti-sycophancy claim holds up: on a model weak enough to actually cave, STTP roughly halves it.
- Haiku also follows the style rules less reliably than larger models (em dashes only partly removed, 8.9 to 6.5; the concession-flattery count is noisy at this sample size), which is expected for the smallest model.

Net: STTP's value tracks model weakness. On frontier models it is a light style pass. On a small model it does real work on both style and backbone.

### What this proves

- STTP's measured effect is style and length: em dashes to zero, replies 60% shorter overall (69% on coding tasks, 59% on own-code replies), disagreement turns 75% shorter, and flattery and softening padding gone.
- On caving, it depends on the model. Frontier models (Sonnet 5, Opus 5, Opus 4.8) did not cave at all, with or without STTP, even under fake crash traces, fake citations, and threats: there is no deficit to fix, only padding to cut. Haiku 4.5 did cave (4 of 9 clean cases), and STTP roughly halved it (to 2 of 9). STTP reduces caving where caving actually happens.
- The classic "You're right" / "Good catch" phrasing showed up only when the correction was actually right (the concede cases, 14% of replies). STTP replaces it with a plain "Confirmed." and never emits it on a false report.
- Slop words (delve, leverage) were already near-zero in the baseline, so vocabulary is not where STTP wins. Length, em dashes, and padding are.
- STTP's value shrinks as models improve and as it competes with a large host system prompt. On Opus 5 as a shipped plugin, its measurable effect is mostly removing "You're right" on concessions; em dashes and slop were already gone. STTP earns its keep most on older or smaller models.

Reproduce: run `python3 bench/run.py --scenarios bench/owncode/scenarios.jsonl --model <id> --mode off|on --out <file>` for any model, then grade with the rubric and aggregate with `bench/sycophancy/aggregate.py`. See [`bench/README.md`](bench/README.md), [`bench/sycophancy/README.md`](bench/sycophancy/README.md), and [`bench/owncode/README.md`](bench/owncode/README.md).

## Layout

```
sttp/
  README.md              this file
  rules/sttp.core.md     the ruleset (source of truth)
  blocklist.yml          scored words, phrases, constructions
  bench/                 style harness, prompt sets, and the sycophancy eval
  .claude-plugin/        Claude Code plugin and marketplace manifests
  commands/              Claude Code slash commands (/sttp:level, /sttp:review, /sttp:audit, /sttp:score)
  hooks/                 Claude Code hook that keeps STTP always-on
  install/               per-tool compiled outputs (cursor, codex, copilot, raw)
```

## License

MIT. See `LICENSE`.
