---
description: Set or disable the STTP level for this session.
argument-hint: "[off|1.0|1.1|2]"
---

Load `${CLAUDE_PLUGIN_ROOT}/rules/sttp.core.md` and apply it as a standing instruction for the rest of the session.

Argument: `$ARGUMENTS` is the level to set. Accepted values: `1.0`, `1.1`, `2`, `off`.

- No argument: set STTP/1.1 (Style plus Backbone, the default).
- `1.0`: Style only. Slop Filter active, Pushback Ladder off.
- `1.1`: Style plus Backbone. Both sections active.
- `2`: Terse mode. Everything in 1.1, plus no preamble, no postamble, one-line acknowledgments, minimum viable words.
- `off`: drop the ruleset. Return to normal behavior.

After setting the level, state the active level in one line and nothing else. No preamble, no summary of what STTP is.
