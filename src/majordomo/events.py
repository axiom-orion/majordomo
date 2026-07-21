"""Events-domain tools for the concierge, via the BAI events MCP (@bai/mcp).

Majordomo answers guests; when a request needs domain reasoning — "can you host
our 300-person conference?", "what's the room block?", "how many servers for a
plated dinner?" — it consults the governed BAI events surface over MCP. Every
call the MCP fulfils is sealed into a GreenTeamGo receipt on its side, so the
concierge's domain claims are provable, not improvised.

Config: BAI_MCP_CMD / BAI_MCP_ARGS / BAI_MCP_CWD point at the built server
(default: `node dist/server.js` in the bai-mcp repo). Requires the `mcp` client
package (`pip install mcp`) and a built bai-mcp (`npm run build`).
"""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass

# Tools the concierge may consult, with a one-line intent for prompt/tool selection.
EVENT_TOOLS = {
    "absorb_citywide": "Can the market house a group of this size? peak rooms, block hotels, stress.",
    "venue_cluster_capacity": "How many rooms can a hotel cluster assemble (the anchor block)?",
    "compute_drop": "Will banquet service reach the far tables? presence ratio for a room + service style.",
    "deal_shifts": "Allocate open shifts to servers for a shift drop.",
    "advancement": "What training moves a server up the house ladder?",
    "package_bar_pricing": "Is a hosted package bar priced to cover its pours?",
}


@dataclass
class EventsClient:
    command: str = os.environ.get("BAI_MCP_CMD", "node")
    args: tuple[str, ...] = tuple((os.environ.get("BAI_MCP_ARGS") or "dist/server.js").split())
    cwd: str | None = os.environ.get("BAI_MCP_CWD")

    async def _call(self, name: str, arguments: dict) -> dict:
        # Imported lazily so majordomo runs without the mcp client when events aren't used.
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        params = StdioServerParameters(command=self.command, args=list(self.args), cwd=self.cwd)
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                res = await session.call_tool(name, arguments)
                text = res.content[0].text if res.content else "{}"
                return json.loads(text)  # {"result": ..., "receipt": {...}}

    def consult(self, name: str, arguments: dict) -> dict:
        """Sync entry for the concierge loop. Returns {result, receipt}; the
        receipt is the proof the domain claim was governed."""
        if name not in EVENT_TOOLS:
            raise ValueError(f"unknown events tool {name!r}; known: {sorted(EVENT_TOOLS)}")
        return asyncio.run(self._call(name, arguments))


def tool_catalog() -> str:
    """A prompt-ready description of the events tools, for the concierge to pick from."""
    return "\n".join(f"- {n}: {desc}" for n, desc in EVENT_TOOLS.items())
