"""The concierge agent: recall -> respond -> remember.

Each session is a conversation with a returning guest. Before answering, the
agent recalls governed memories relevant to the request; after the session
ends, it distills the transcript back into memory. Sessions are the unit of
persistence — the whole point is what carries across them.
"""

from dataclasses import dataclass, field

from majordomo.engine import MemoryEngine, RememberReport

CONCIERGE_SYSTEM = """[concierge] You are Majordomo, the head concierge of the
Grand Meridian hotel, speaking with a returning guest. You are warm, precise,
and never generic. Ground every recommendation in what you know about this
guest — their remembered preferences are listed below. If a remembered
preference is relevant, act on it without being asked. If you know nothing
relevant, ask one good question instead of guessing.

What you remember about this guest:
{memories}"""


@dataclass
class Session:
    guest_id: str
    session_id: str
    engine: MemoryEngine
    turns: list[tuple[str, str]] = field(default_factory=list)

    def ask(self, message: str) -> tuple[str, list[dict]]:
        """One guest turn: recall relevant memories, respond grounded in them."""
        recalled = self.engine.recall(self.guest_id, message)
        memory_block = "\n".join(f"- {m['content']}" for m in recalled) or "- (no prior memories)"
        reply = self.engine.client.chat(
            CONCIERGE_SYSTEM.format(memories=memory_block),
            "\n".join(f"Guest: {g}\nMajordomo: {r}" for g, r in self.turns[-6:])
            + f"\nGuest: {message}",
        )
        self.turns.append((message, reply))
        return reply, recalled

    def close(self) -> RememberReport:
        """End of session: distill the transcript into governed memory."""
        transcript = "\n".join(f"Guest: {g}\nMajordomo: {r}" for g, r in self.turns)
        if not transcript:
            return RememberReport([], [], [])
        return self.engine.remember(self.guest_id, transcript, self.session_id)
