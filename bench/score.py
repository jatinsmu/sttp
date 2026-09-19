#!/usr/bin/env python3
"""STTP scoring harness. Scores agent RESPONSES supplied to it.

Does not call any model or provider. Generation is the caller's job:
run your agent, save its output, then score the output with this file.

Usage:
  python score.py <file.txt | ->        score one reply, print status codes
  python score.py --audit <file>        density score and flagged tokens
  python score.py --bench <file.jsonl>  aggregate stat card over many replies
  python score.py <file> --budget N     override the length budget (default 250)
"""

import argparse
import json
import os
import re
import sys

import yaml

BLOCKLIST_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "blocklist.yml")
FLATTERY_WINDOW_CHARS = 120
DEFAULT_BUDGET = 250

# blocklist.yml writes em dashes as an escaped literal, not the actual
# character, so the file's own patterns can't be used here. Match the real
# characters directly, independent of how the group is declared.
EM_DASH_CHARS = "\u2014\u2013"


def load_blocklist(path=BLOCKLIST_PATH):
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    groups = {}
    for key, val in data.items():
        if key == "version" or not isinstance(val, dict):
            continue
        if "weight" in val and "match" in val:
            groups[key] = val
            continue
        # nested groups, e.g. punctuation.em_dash
        for subkey, subval in val.items():
            if isinstance(subval, dict) and "weight" in subval and "match" in subval:
                groups[f"{key}.{subkey}"] = subval
    return groups


def literal_pattern(term):
    # word-boundary the side that starts/ends on a word char; punctuation
    # already acts as its own boundary, so a \b there would misfire.
    left = r"\b" if term[0].isalnum() else ""
    right = r"\b" if term[-1].isalnum() else ""
    return left + re.escape(term) + right


def line_of(text, index):
    return text.count("\n", 0, index) + 1


def find_literal_hits(text, terms, window=None):
    haystack = text if window is None else text[:window]
    hits = []
    for term in terms:
        pattern = re.compile(literal_pattern(term), re.IGNORECASE)
        for m in pattern.finditer(haystack):
            hits.append({"term": term, "line": line_of(text, m.start()), "text": m.group()})
    return hits


def find_word_hits(text, terms):
    hits = []
    for term in terms:
        pattern = re.compile(r"\b" + re.escape(term) + r"\b", re.IGNORECASE)
        for m in pattern.finditer(text):
            hits.append({"term": term, "line": line_of(text, m.start()), "text": m.group()})
    return hits


def find_regex_hits(lines, patterns):
    hits = []
    for pat in patterns:
        compiled = re.compile(pat, re.IGNORECASE)
        for line_no, line in enumerate(lines, start=1):
            for m in compiled.finditer(line):
                hits.append({"term": pat, "line": line_no, "text": m.group()})
    return hits


def find_sentence_start_hits(lines, terms):
    hits = []
    for line_no, line in enumerate(lines, start=1):
        for chunk in re.split(r"(?<=[.!?])\s+", line):
            stripped = chunk.lstrip(" \t\"'`*-•").lstrip("0123456789.) ")
            for term in terms:
                if re.match(re.escape(term) + r"\b", stripped, re.IGNORECASE):
                    hits.append({"term": term, "line": line_no, "text": chunk.strip()})
    return hits


def find_em_dash_hits(lines):
    hits = []
    for line_no, line in enumerate(lines, start=1):
        for ch in line:
            if ch in EM_DASH_CHARS:
                hits.append({"term": ch, "line": line_no, "text": ch})
    return hits


def score_text(text, blocklist=None, budget=DEFAULT_BUDGET):
    blocklist = blocklist or load_blocklist()
    lines = text.split("\n")
    word_count = len(text.split())

    group_hits = {}
    for name, group in blocklist.items():
        if name == "punctuation.em_dash":
            group_hits[name] = find_em_dash_hits(lines)
            continue
        match_type = group["match"]
        if match_type == "literal":
            window = FLATTERY_WINDOW_CHARS if name == "flattery_openers" else None
            group_hits[name] = find_literal_hits(text, group.get("terms", []), window)
        elif match_type == "word":
            group_hits[name] = find_word_hits(text, group.get("terms", []))
        elif match_type == "regex":
            group_hits[name] = find_regex_hits(lines, group.get("patterns", []))
        elif match_type == "sentence_start":
            group_hits[name] = find_sentence_start_hits(lines, group.get("terms", []))
        else:
            group_hits[name] = []

    group_counts = {name: len(hits) for name, hits in group_hits.items()}
    weighted_total = sum(blocklist[name]["weight"] * count for name, count in group_counts.items())
    slop_density = (weighted_total / word_count * 1000) if word_count else 0.0

    return {
        "word_count": word_count,
        "em_dash_count": group_counts.get("punctuation.em_dash", 0),
        "flattery_opener": group_counts.get("flattery_openers", 0) > 0,
        "group_hits": group_hits,
        "group_counts": group_counts,
        "weighted_total": weighted_total,
        "slop_density": slop_density,
        "over_budget": word_count > budget,
        "budget": budget,
    }


SLOP_GROUPS = ["tier1_words", "banned_phrases", "constructions", "glue_phrases", "transition_openers"]


def status_rows(result, budget):
    rows = []

    if result["flattery_opener"]:
        hits = result["group_hits"]["flattery_openers"]
        terms = sorted({h["text"] for h in hits})
        rows.append(("403 Flattery Opener", f"line {hits[0]['line']}", ", ".join(f'"{t}"' for t in terms[:3])))

    if result["em_dash_count"]:
        hits = result["group_hits"]["punctuation.em_dash"]
        rows.append(("451 Em Dash Detected", f"line {hits[0]['line']}", f"{result['em_dash_count']} found"))

    praise_hits = result["group_hits"].get("unearned_praise", [])
    if praise_hits:
        terms = sorted({h["text"] for h in praise_hits})
        rows.append(("401 Unearned Praise", f"line {praise_hits[0]['line']}", ", ".join(f'"{t}"' for t in terms[:3])))

    slop_hits = [h for name in SLOP_GROUPS for h in result["group_hits"].get(name, [])]
    if slop_hits:
        terms = sorted({h["text"] for h in slop_hits})
        line = min(h["line"] for h in slop_hits)
        rows.append(("420 Slop", f"line {line}", ", ".join(f'"{t}"' for t in terms[:5])))

    if result["over_budget"]:
        rows.append(("413 Response Too Long", "-", f"{result['word_count']} words, budget {budget}"))

    if not rows:
        rows.append(("200 OK", "-", f"{result['word_count']} words clean"))

    return rows


def print_report(text, blocklist, budget):
    result = score_text(text, blocklist, budget)
    print("STTP/1.1 score")
    for code, loc, detail in status_rows(result, budget):
        print(f"{code:<24} {loc:<8} {detail}")


def print_audit(text, blocklist):
    result = score_text(text, blocklist)
    print(f"slop density: {result['slop_density']:.2f} / 1000 words")
    print(f"em dashes: {result['em_dash_count']}")
    print(f"words: {result['word_count']}")
    print("flagged:")
    flagged = False
    for name, hits in result["group_hits"].items():
        if not hits:
            continue
        flagged = True
        terms = sorted({h["text"] for h in hits})
        print(f"  {name}: {', '.join(terms)} ({len(hits)})")
    if not flagged:
        print("  none")


def run_bench(path, blocklist):
    records = []
    with open_maybe_stdin(path) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    n = len(records)
    if n == 0:
        print("no responses")
        return

    flattery = 0
    density_sum = 0.0
    em_per_1000_sum = 0.0
    words_sum = 0

    for rec in records:
        result = score_text(rec.get("response", ""), blocklist)
        if result["flattery_opener"]:
            flattery += 1
        density_sum += result["slop_density"]
        wc = result["word_count"]
        em_per_1000_sum += (result["em_dash_count"] / wc * 1000) if wc else 0.0
        words_sum += wc

    print(f"STTP bench: {n} responses")
    print(f"flattery-opener rate:  {flattery / n * 100:.1f}%")
    print(f"mean slop density:     {density_sum / n:.2f} / 1000 words")
    print(f"mean em dashes:        {em_per_1000_sum / n:.2f} / 1000 words")
    print(f"mean words:            {words_sum / n:.1f}")


def open_maybe_stdin(path):
    if path == "-":
        return sys.stdin
    return open(path, encoding="utf-8")


def read_text(path):
    with open_maybe_stdin(path) as f:
        return f.read()


def main():
    parser = argparse.ArgumentParser(description="STTP scoring harness")
    parser.add_argument("file", nargs="?", help="text file to score, or - for stdin")
    parser.add_argument("--audit", metavar="FILE", help="print density score and flagged tokens for one text")
    parser.add_argument("--bench", metavar="FILE", help="score a JSONL file of {id, response} lines")
    parser.add_argument("--budget", type=int, default=DEFAULT_BUDGET, help="length budget in words (default 250)")
    args = parser.parse_args()

    blocklist = load_blocklist()

    if args.bench:
        run_bench(args.bench, blocklist)
    elif args.audit:
        print_audit(read_text(args.audit), blocklist)
    elif args.file:
        print_report(read_text(args.file), blocklist, args.budget)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
