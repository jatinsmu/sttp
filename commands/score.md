---
description: Run the STTP benchmark and print the stat card.
argument-hint: "<file.jsonl>"
---

Run the STTP benchmark comparing STTP off vs on, following `${CLAUDE_PLUGIN_ROOT}/bench/README.md`.

1. If saved response JSONL files for the `${CLAUDE_PLUGIN_ROOT}/bench/prompts/` sets don't already exist for this run, generate them: answer each prompt set once with STTP off and once with STTP on, saving `{"id", "response"}` lines per prompt set per condition.
2. Score each file with:

```
python3 "${CLAUDE_PLUGIN_ROOT}/bench/score.py" --bench $ARGUMENTS
```

3. For `false-premise.jsonl` and `pushback.jsonl`, grade each response pass/fail against the rubric in `${CLAUDE_PLUGIN_ROOT}/bench/README.md` (compare to the `correct` / `correct_position` field). Report the pass rate for each set, off vs on.
4. Print a single comparison stat card: flattery-opener rate, mean slop density, mean em dashes per 1000 words, mean words per response, false-premise-caught rate, held-under-pushback rate, each as off versus on.

Do not claim a metric you didn't actually run. If a step wasn't run (e.g. no saved responses to score), say what's missing instead of estimating a number.
