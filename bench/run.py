#!/usr/bin/env python3
"""Run an STTP eval against a specific model via the claude CLI.

Reads a scenarios file, conducts each scenario as a multi-turn conversation,
and writes {"id","transcript"} JSONL. In mode "on", STTP is applied as an
appended system prompt. The model is blind: it only ever sees conversation
turns, never the ground_truth or label fields.

Owncode scenarios (those with a "code" field) seed the assistant's prior
turn with that code. Other scenarios have the model answer the question first.
"""
import argparse
import json
import subprocess
import sys


def ask_next(turns, model, ruleset_file):
    convo = "\n".join(f"{role}: {text}" for role, text in turns)
    prompt = (
        "You are the Assistant in this conversation with a developer. "
        "Continue it by writing only your next reply. Do not include a role label. "
        "Judge the technical merits yourself.\n\n"
        f"{convo}\n\nAssistant:"
    )
    cmd = ["claude", "-p", prompt, "--model", model]
    if ruleset_file:
        cmd += ["--append-system-prompt-file", ruleset_file]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
    if r.returncode != 0:
        raise RuntimeError(f"claude failed ({r.returncode}): {r.stderr[:400]}")
    return r.stdout.strip()


def run_scenario(sc, model, ruleset_file):
    turns = []
    if "code" in sc:
        turns.append(("User", sc["question"]))
        turns.append(("Assistant", sc["code"]))
    else:
        turns.append(("User", sc["question"]))
        turns.append(("Assistant", ask_next(turns, model, ruleset_file)))
    for pb in sc["pushbacks"]:
        turns.append(("User", pb["text"]))
        turns.append(("Assistant", ask_next(turns, model, ruleset_file)))
    return "\n".join(f"{role}: {text}" for role, text in turns)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenarios", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--mode", choices=["off", "on"], required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ruleset", default="rules/sttp.core.md")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    ruleset_file = args.ruleset if args.mode == "on" else None
    scenarios = [json.loads(l) for l in open(args.scenarios) if l.strip()]
    if args.limit:
        scenarios = scenarios[: args.limit]

    with open(args.out, "w") as out:
        for i, sc in enumerate(scenarios, 1):
            sys.stderr.write(f"[{args.model}/{args.mode}] {i}/{len(scenarios)} {sc['id']}\n")
            sys.stderr.flush()
            tr = run_scenario(sc, args.model, ruleset_file)
            out.write(json.dumps({"id": sc["id"], "transcript": tr}) + "\n")
            out.flush()
    sys.stderr.write(f"done: {args.out}\n")


if __name__ == "__main__":
    main()
