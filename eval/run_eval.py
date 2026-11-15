"""Run the Ask Nhi eval set against the agent and print a score.

Usage: python -m eval.run_eval [--delay SECONDS]
Needs the real API keys in .env. 12 questions, a few cents on Haiku.
Use --delay 25 if your Voyage account has no payment method (3 requests/minute limit).
"""

import argparse
import json
import logging
import re
import time
from pathlib import Path

from agent.graph import ask, build_graph

HERE = Path(__file__).parent
PRONOUNS = re.compile(r"\b(she|her|hers|herself|he|him|his)\b", re.IGNORECASE)
# Nhi's rule: never say "the sources/excerpts don't say...", just leave the missing detail out.
META_PHRASES = re.compile(
    r"\b(excerpts?|sources?)\b[^.\n]{0,25}\b(don't|do not|doesn't|does not|didn't)\b[^.\n]{0,15}\b(say|include|mention|describe|show|specify|list|cover)",
    re.IGNORECASE,
)
REFUSAL_HINTS = ("can't", "cannot", "can only", "not able", "don't share", "won't", "not something")


def grade(case: dict, result: dict) -> dict:
    answer = result["answer"]
    lower = answer.lower()
    cited = set(re.findall(r"\[([a-z0-9-]+)(?:#[^\]]*)?\]", answer))
    checks = {
        "calls_nhi_by_name": not PRONOUNS.search(answer),
        "no_meta_phrases": not META_PHRASES.search(answer),
    }
    if case.get("refuse"):
        checks["refused"] = any(h in lower for h in REFUSAL_HINTS)
    else:
        expected = set(case.get("expect_sources", []))
        if expected:
            checks["cites_expected_source"] = bool(expected & cited)
        for term in case.get("must_mention", []):
            # "5|five" accepts either spelling
            checks[f"mentions:{term}"] = any(alt.strip().lower() in lower for alt in term.split("|"))
        checks["used_search"] = "search_portfolio" in result["tool_calls"]
    return {"q": case["q"], "passed": all(checks.values()), "checks": checks, "answer": answer, "cited": sorted(cited), "tool_errors": result.get("tool_errors", [])}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--delay", type=float, default=0, help="seconds to wait between questions")
    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING, format="      [log] %(message)s")

    cases = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))["cases"]
    graph = build_graph()
    out = HERE / f"results-{int(time.time())}.json"
    results = []
    for i, case in enumerate(cases):
        if i and args.delay:
            time.sleep(args.delay)
        try:
            r = grade(case, ask(case["q"], graph))
        except Exception as e:  # keep going; one failing question shouldn't hide the rest
            r = {"q": case["q"], "passed": False, "checks": {"error": False}, "answer": f"{type(e).__name__}: {e}", "cited": []}
        results.append(r)
        print(f"{'PASS' if r['passed'] else 'FAIL'}  {case['q']}")
        for err in r.get("tool_errors", []):
            print(f"      tool error: {err}")
        for name, ok in r["checks"].items():
            if not ok:
                print(f"      failed {name}" + (f": {r['answer'][:120]}" if name == "error" else ""))
        out.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    passed = sum(r["passed"] for r in results)
    print(f"\n{passed}/{len(results)} cases passed")
    print(f"Answers and checks: {out}")


if __name__ == "__main__":
    main()
