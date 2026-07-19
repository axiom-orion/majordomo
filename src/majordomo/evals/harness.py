"""Cross-session memory evaluation — the proof behind the MemoryAgent track.

The track asks builders to demonstrate "efficient memory storage and retrieval,
timely forgetting of outdated information, and recalling critical memories
within limited context windows" and "increasingly accurate decisions across
multi-turn, cross-session interactions." This harness measures exactly those,
running the same scripted guests through TWO agents:

  governed : Majordomo's full engine (dedupe + contradiction supersede)
  naive    : append-only memory (governance off) — the baseline

What we measure per stay (verified on real Qwen, not the mock):

  1. STALE-IN-RECALL  — after a guest changes a preference, does the agent's
     limited-context recall still surface the *superseded* fact? Governed memory
     retires it (0); append-only memory keeps leaking it into every decision.
     This is "timely forgetting" + "critical memories in a limited window".
  2. ACTIVE STORE SIZE — governed dedupes/retires, so its store stays lean;
     append-only grows unbounded. This is "efficient memory storage".
  3. COVERAGE ACCURACY — fraction of ALL the guest's facts the agent answers
     correctly, which rises as it accumulates experience across sessions.
     ("increasingly accurate decisions across cross-session interactions".)

Honest finding: with a capable model, BOTH agents answer known facts correctly
(the model recovers the current fact even from a polluted recall) — so raw
answer-accuracy does not separate them. What separates them is recall hygiene:
the append-only agent makes every decision on a store full of contradicted,
duplicated memories, with no audit trail. Governance fixes that structurally.

Output: data/eval_results.json (+ chart for the demo video).
"""

import json
from pathlib import Path

from majordomo.agent import Session
from majordomo.config import settings
from majordomo.engine import MemoryEngine
from majordomo.evals.personas import PERSONAS
from majordomo.llm import get_client
from majordomo.store import MemoryStore

JUDGE_SYSTEM = """[quizjudge] You grade a hotel concierge's answer against
ground truth. Return JSON: {{"correct": true|false}}. The answer is correct only
if it contains the substance of the expected fact "{expect}". An answer that
hedges, says it doesn't know, or states a different/stale fact is incorrect."""


def _expected(quiz: dict, session_idx: int) -> str:
    expect = quiz["expect"]
    for update_at in sorted(quiz.get("updates", {})):
        if session_idx >= update_at:
            expect = quiz["updates"][update_at]
    return expect


def _update_done(quiz: dict, session_idx: int) -> bool:
    ups = quiz.get("updates")
    return bool(ups) and session_idx >= max(ups)


def _quiz_agent(engine: MemoryEngine, judge, guest_id: str, quiz: list[dict],
                session_idx: int) -> dict:
    """Quiz every fact. Returns answerable/coverage accuracy plus the number of
    stale (superseded) memories the agent surfaced into recall this stay."""
    answerable_correct = answerable_total = 0
    coverage_correct = coverage_total = 0
    stale_in_recall = 0
    details = []
    probe = Session(guest_id=guest_id, session_id=f"quiz-{session_idx}", engine=engine)
    for q in quiz:
        expect = _expected(q, session_idx)
        answer, recalled = probe.ask(q["q"])
        verdict_raw = judge.chat(
            JUDGE_SYSTEM.format(expect=expect),
            f'Question: "{q["q"]}"\nExpected fact: "{expect}"\nConcierge answer: "{answer}"',
            model=settings.judge_model, json_mode=True,
        )
        try:
            parsed = json.loads(verdict_raw)
            ok = bool(parsed.get("correct", False)) if isinstance(parsed, dict) else bool(parsed)
        except json.JSONDecodeError:
            ok = False

        # Coverage: every fact counts every stay (unrevealed facts score wrong,
        # so accuracy climbs as the agent accumulates experience).
        coverage_total += 1
        coverage_correct += ok
        # Answerable: only facts revealed by now (both agents ~always right here).
        if session_idx >= q["answerable_from"]:
            answerable_total += 1
            answerable_correct += ok
        # Stale-in-recall: once a preference has been changed, count superseded
        # concepts still surfacing in the limited recall window.
        if _update_done(q, session_idx):
            # A recalled memory is STALE only if it carries the outdated concept
            # and NOT the current one — so "matcha instead of cappuccino" (the
            # current preference, which merely names the old drink) does not count.
            def _is_stale(text: str) -> bool:
                low = text.lower()
                return (any(t in low for t in q.get("stale_terms", []))
                        and not any(t in low for t in q.get("current_terms", [])))
            stale_hits = sum(1 for m in recalled if _is_stale(m["content"]))
            stale_in_recall += stale_hits
            details.append({
                "q": q["q"], "expected": expect, "correct": ok,
                "stale_in_recall": stale_hits,
                "recalled": [m["content"] for m in recalled],
            })
        else:
            details.append({"q": q["q"], "expected": expect, "correct": ok})
    # Quiz probes are never remembered — probe.close() intentionally not called.
    return {
        "answerable_accuracy": round(answerable_correct / answerable_total, 3) if answerable_total else None,
        "coverage_accuracy": round(coverage_correct / coverage_total, 3) if coverage_total else None,
        "stale_in_recall": stale_in_recall,
        "details": details,
    }


def run_persona(persona: dict, govern: bool) -> dict:
    client = get_client()
    store = MemoryStore(Path(":memory:"))
    engine = MemoryEngine(store=store, client=client, govern=govern)
    guest = persona["guest_id"]

    per_session = []
    for idx, utterances in enumerate(persona["sessions"], start=1):
        session = Session(guest_id=guest, session_id=f"stay-{idx}", engine=engine)
        for line in utterances:
            session.ask(line)
        report = session.close()
        graded = _quiz_agent(engine, client, guest, persona["quiz"], idx)
        per_session.append({
            "session": idx,
            "answerable_accuracy": graded["answerable_accuracy"],
            "coverage_accuracy": graded["coverage_accuracy"],
            "stale_in_recall": graded["stale_in_recall"],
            "active_rows": len(store.active(guest)),
            "stored": len(report.stored), "reinforced": len(report.reinforced),
            "superseded": len(report.superseded),
            "details": graded["details"],
        })
    return {
        "persona": persona["name"], "guest_id": guest,
        "mode": "governed" if govern else "naive",
        "per_session": per_session,
        "final_active_rows": len(store.active(guest)),
        "final_total_rows": len(store.history(guest)),
    }


def _series(results: list[dict], mode: str, field: str, agg: str) -> list[float]:
    n = max(len(r["per_session"]) for r in results)
    out = []
    for i in range(n):
        vals = [r["per_session"][i][field] for r in results
                if r["mode"] == mode and i < len(r["per_session"])
                and r["per_session"][i][field] is not None]
        if not vals:
            out.append(None)
        elif agg == "sum":
            out.append(round(sum(vals), 3))
        else:  # mean
            out.append(round(sum(vals) / len(vals), 3))
    return out


def run(chart: bool = True) -> dict:
    results = []
    for persona in PERSONAS:
        for govern in (True, False):
            results.append(run_persona(persona, govern))

    summary = {
        "backend": settings.llm_backend,
        # Timely forgetting: contradicted memories leaking into recall (want 0).
        "stale_in_recall_by_session": {
            "governed": _series(results, "governed", "stale_in_recall", "sum"),
            "naive": _series(results, "naive", "stale_in_recall", "sum"),
        },
        # Efficient storage: active memory rows carried per guest (want lean).
        "active_rows_by_session": {
            "governed": _series(results, "governed", "active_rows", "mean"),
            "naive": _series(results, "naive", "active_rows", "mean"),
        },
        # Increasingly accurate decisions as experience accumulates.
        "coverage_accuracy_by_session": {
            "governed": _series(results, "governed", "coverage_accuracy", "mean"),
            "naive": _series(results, "naive", "coverage_accuracy", "mean"),
        },
        "results": results,
    }
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    (settings.data_dir / "eval_results.json").write_text(json.dumps(summary, indent=2))

    if chart:
        try:
            _chart(summary, settings.data_dir / "accuracy_curve.png")
            summary["chart"] = str(settings.data_dir / "accuracy_curve.png")
        except ImportError:
            summary["chart"] = "matplotlib not installed - pip install majordomo[charts]"
    return summary


def _chart(summary: dict, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    stale = summary["stale_in_recall_by_session"]
    rows = summary["active_rows_by_session"]
    x = list(range(1, len(stale["governed"]) + 1))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.3))

    ax1.plot(x, stale["governed"], marker="o", linewidth=2.4, color="#16a34a",
             label="Majordomo (governed)")
    ax1.plot(x, stale["naive"], marker="s", linewidth=2.4, linestyle="--", color="#dc2626",
             label="Append-only baseline")
    ax1.set_title("Timely forgetting: stale memories leaking into recall")
    ax1.set_xlabel("Guest stay (session)")
    ax1.set_ylabel("Contradicted memories surfaced into recall")
    ax1.set_xticks(x)
    ax1.set_ylim(bottom=-0.3)
    ax1.grid(alpha=0.3)
    ax1.legend()

    ax2.plot(x, rows["governed"], marker="o", linewidth=2.4, color="#16a34a",
             label="Majordomo (governed)")
    ax2.plot(x, rows["naive"], marker="s", linewidth=2.4, linestyle="--", color="#dc2626",
             label="Append-only baseline")
    ax2.set_title("Efficient storage: active memory rows per guest")
    ax2.set_xlabel("Guest stay (session)")
    ax2.set_ylabel("Active memory rows")
    ax2.set_xticks(x)
    ax2.set_ylim(bottom=0)
    ax2.grid(alpha=0.3)
    ax2.legend()

    backend = summary.get("backend", "")
    src = "live Qwen Cloud" if backend == "qwen" else "deterministic offline harness"
    fig.suptitle(f"Governed vs append-only memory across sessions ({src})", fontsize=12)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
