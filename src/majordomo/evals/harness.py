"""Cross-session accuracy evaluation — the proof behind the track's ask.

The MemoryAgent track calls for "increasingly accurate decisions across
multi-turn, cross-session interactions." This harness measures exactly that,
and runs the same scripted guests through TWO agents:

  governed : Majordomo's full engine (dedupe + contradiction supersede)
  naive    : append-only memory (governance off) — the baseline

After each session, the agent is quizzed on every fact revealed so far; a
judge model grades answers against ground truth. Expected answers re-key when
a guest CHANGES a preference — where append-only memory keeps recalling the
stale fact, and the curves diverge.

Output: per-session accuracy for both modes -> data/eval_results.json
(+ optional matplotlib chart for the demo video).
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


def _quiz_agent(engine: MemoryEngine, judge, guest_id: str, quiz: list[dict],
                session_idx: int) -> tuple[int, int, list[dict]]:
    correct = total = 0
    details = []
    probe = Session(guest_id=guest_id, session_id=f"quiz-{session_idx}", engine=engine)
    for q in quiz:
        if session_idx < q["answerable_from"]:
            continue
        expect = _expected(q, session_idx)
        answer, recalled = probe.ask(q["q"])
        verdict_raw = judge.chat(
            JUDGE_SYSTEM.format(expect=expect),
            f'Question: "{q["q"]}"\nExpected fact: "{expect}"\nConcierge answer: "{answer}"',
            model=settings.judge_model, json_mode=True,
        )
        try:
            ok = json.loads(verdict_raw).get("correct", False)
        except json.JSONDecodeError:
            ok = False
        total += 1
        correct += ok
        details.append({"q": q["q"], "expected": expect, "answer": answer, "correct": ok})
    # Quiz probes are never remembered — probe.close() intentionally not called.
    return correct, total, details


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
        correct, total, details = _quiz_agent(engine, client, guest, persona["quiz"], idx)
        per_session.append({
            "session": idx,
            "accuracy": round(correct / total, 3) if total else None,
            "correct": correct, "total": total,
            "stored": len(report.stored), "reinforced": len(report.reinforced),
            "superseded": len(report.superseded),
            "details": details,
        })
    return {
        "persona": persona["name"], "guest_id": guest,
        "mode": "governed" if govern else "naive",
        "per_session": per_session,
        "final_memory_rows": len(store.history(guest)),
    }


def run(chart: bool = True) -> dict:
    results = []
    for persona in PERSONAS:
        for govern in (True, False):
            results.append(run_persona(persona, govern))

    def curve(mode: str) -> list[float]:
        n = max(len(r["per_session"]) for r in results)
        out = []
        for i in range(n):
            vals = [r["per_session"][i]["accuracy"] for r in results
                    if r["mode"] == mode and i < len(r["per_session"])
                    and r["per_session"][i]["accuracy"] is not None]
            out.append(round(sum(vals) / len(vals), 3) if vals else None)
        return out

    summary = {
        "backend": settings.llm_backend,
        "governed_accuracy_by_session": curve("governed"),
        "naive_accuracy_by_session": curve("naive"),
        "results": results,
    }
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    out_path = settings.data_dir / "eval_results.json"
    out_path.write_text(json.dumps(summary, indent=2))

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

    gov, naive = summary["governed_accuracy_by_session"], summary["naive_accuracy_by_session"]
    x = list(range(1, len(gov) + 1))
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot(x, gov, marker="o", linewidth=2.2, label="Majordomo (governed memory)")
    ax.plot(x, naive, marker="s", linewidth=2.2, linestyle="--", label="Baseline (append-only memory)")
    ax.set_xlabel("Guest stay (session)")
    ax.set_ylabel("Decision accuracy")
    ax.set_title("Accuracy across sessions — governed vs append-only memory")
    ax.set_xticks(x)
    ax.set_ylim(0, 1.05)
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
