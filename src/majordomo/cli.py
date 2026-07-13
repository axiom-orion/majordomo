"""Majordomo CLI.

  chat     interactive concierge session for a guest (persists memory)
  memory   inspect a guest's memory: active, superseded, provenance
  eval     run the cross-session accuracy harness (governed vs naive)
  demo     one-shot scripted walkthrough for the video
"""

import json

import click


@click.group()
def cli():
    """Majordomo — the concierge that never forgets."""


@cli.command()
@click.option("--guest", required=True, help="Guest id, e.g. g-voss")
@click.option("--session", "session_id", default=None, help="Session id (default: auto)")
def chat(guest, session_id):
    """Interactive session; memory is distilled and governed on exit."""
    import time

    from majordomo.agent import Session
    from majordomo.engine import MemoryEngine

    session = Session(
        guest_id=guest,
        session_id=session_id or f"chat-{int(time.time())}",
        engine=MemoryEngine(),
    )
    click.echo("Majordomo at your service. (empty line to end the session)")
    while True:
        msg = click.prompt("guest", default="", show_default=False)
        if not msg:
            break
        reply, recalled = session.ask(msg)
        if recalled:
            click.secho("  [recalled: " + "; ".join(m["content"] for m in recalled[:3]) + "]",
                        fg="cyan")
        click.echo(f"majordomo: {reply}")
    report = session.close()
    click.secho(
        f"\nmemory update — stored: {len(report.stored)}, reinforced: {len(report.reinforced)}, "
        f"superseded: {len(report.superseded)}", fg="green")
    for old, new in report.superseded:
        click.secho(f"  superseded: '{old}'  ->  '{new}'", fg="yellow")


@cli.command()
@click.option("--guest", required=True)
def memory(guest):
    """Show the guest's full memory ledger: active + superseded with provenance."""
    from majordomo.store import MemoryStore

    store = MemoryStore()
    rows = store.history(guest)
    if not rows:
        click.echo("no memories for this guest")
        return
    for r in rows:
        status = f"SUPERSEDED by #{r['superseded_by']} ({r['supersede_reason']})" \
            if r["superseded_by"] else "active"
        click.echo(f"#{r['id']:>3} [{r['kind']:<15}] x{r['reinforcements']} "
                   f"({r['source_session']}) {status}\n     {r['content']}")


@cli.command("eval")
@click.option("--no-chart", is_flag=True)
def eval_cmd(no_chart):
    """Cross-session accuracy: Majordomo (governed) vs append-only baseline."""
    from majordomo.evals.harness import run

    summary = run(chart=not no_chart)
    click.echo(json.dumps(
        {k: v for k, v in summary.items() if k != "results"}, indent=2))
    for r in summary["results"]:
        curve = [s["accuracy"] for s in r["per_session"]]
        click.echo(f"{r['persona']:<16} {r['mode']:<9} accuracy by session: {curve} "
                   f"(memory rows: {r['final_memory_rows']})")


@cli.command()
def demo():
    """Scripted three-stay walkthrough of one guest (for the demo video)."""
    from pathlib import Path

    from majordomo.agent import Session
    from majordomo.engine import MemoryEngine
    from majordomo.evals.personas import PERSONAS
    from majordomo.store import MemoryStore

    persona = PERSONAS[0]
    engine = MemoryEngine(store=MemoryStore(Path(":memory:")))
    for idx, utterances in enumerate(persona["sessions"], start=1):
        click.secho(f"\n=== Stay {idx}: {persona['name']} ===", bold=True)
        session = Session(persona["guest_id"], f"stay-{idx}", engine)
        for line in utterances:
            reply, recalled = session.ask(line)
            click.echo(f"guest: {line}")
            if recalled:
                click.secho("  [recalled: " + "; ".join(m["content"] for m in recalled[:2]) + "]",
                            fg="cyan")
            click.echo(f"majordomo: {reply}")
        report = session.close()
        click.secho(f"memory — stored {len(report.stored)}, reinforced {len(report.reinforced)}, "
                    f"superseded {len(report.superseded)}", fg="green")
        for old, new in report.superseded:
            click.secho(f"  superseded: '{old}' -> '{new}'", fg="yellow")


if __name__ == "__main__":
    cli()
