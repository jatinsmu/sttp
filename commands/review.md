---
description: Scan the last reply, a diff, or a PR for backbone and slop violations.
argument-hint: "[file|diff|PR reference]"
---

Review the target for STTP violations. Target is `$ARGUMENTS` if given (a file, a diff, or a PR reference); otherwise review the assistant's last reply in this conversation.

Check against `${CLAUDE_PLUGIN_ROOT}/rules/sttp.core.md` and `${CLAUDE_PLUGIN_ROOT}/blocklist.yml`:

- Backbone violations: agreement or reversal without checking for a false premise first, praise before or instead of a correction, capitulation under pushback with no new evidence.
- Style violations: em dashes, flattery openers, Tier-1 slop words and banned constructions from `${CLAUDE_PLUGIN_ROOT}/blocklist.yml`, unearned praise, stacked filler transitions, unrequested preamble or postamble.

For anything mechanically checkable (em dashes, blocklist terms, word count against a length budget), prefer running `python3 "${CLAUDE_PLUGIN_ROOT}/bench/score.py"` over the text rather than eyeballing it, if the text is available as a file.

Report findings as STTP status-code rows, one per violation found, in this format:

```
STTP/1.1 review
403 Flattery Opener      line 1   "You're absolutely right!"
451 Em Dash Detected     line 4   1 found
420 Slop                 line 7   "leverage", "robust"
400 Sycophancy           line 9   agreed with a false premise, no correction
413 Response Too Long    -        612 words, budget 250
200 OK                   -        3 sections clean
```

Use only the codes that apply: `200 OK`, `400 Sycophancy`, `401 Unearned Praise`, `403 Flattery Opener`, `413 Response Too Long`, `420 Slop`, `431 Preamble Too Large`, `451 Em Dash Detected`. If nothing is wrong, print a single `200 OK` row. Do not add commentary before or after the table.
