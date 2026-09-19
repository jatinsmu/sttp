---
description: Score a file, doc, or repo of AI-written prose for slop density.
argument-hint: "<file|directory|glob>"
---

Audit `$ARGUMENTS` (a file, directory, or glob) for slop density.

If the target is a single text file, run:

```
python3 "${CLAUDE_PLUGIN_ROOT}/bench/score.py" --audit $ARGUMENTS
```

If the target is a directory or repo, find the relevant prose files (docs, READMEs, PR descriptions, commit messages as applicable) and run the command above with `--audit` on each, then summarize across files: which have the highest slop density, and which flagged tokens repeat most often.

Report the density score, word count, em dash count, and the flagged tokens by group, exactly as `score.py` prints them. Do not soften or reinterpret the numbers. If a file is clean, say so in one line.
