"""LLM backends.

QwenClient talks to Qwen Cloud's OpenAI-compatible endpoint over plain httpx —
no provider SDK shim, one dependency. MockClient is a deterministic offline
backend so the entire pipeline (memory governance, recall, evals, CLI) runs
and tests with zero API keys.
"""

import hashlib
import json
import math
import re
import time

import httpx

from majordomo.config import settings

# Transient failures worth retrying: network read/connect timeouts and the
# server's own overload/ratelimit responses. A slow qwen3.7-max reasoning call
# or a single 429 should not abort a whole eval — or a live demo mid-recording.
_RETRY_STATUS = {429, 500, 502, 503, 504}
_MAX_ATTEMPTS = 4

_TOKEN = re.compile(r"[a-z]{3,}")
_SUFFIXES = ("ically", "ally", "ies", "ing", "ely", "ed", "ly", "es", "ic", "s", "y")
_STOPWORDS = {
    "the", "and", "for", "you", "your", "with", "that", "this", "these", "those",
    "could", "would", "should", "will", "can", "may", "might", "have", "has",
    "was", "were", "are", "not", "but", "all", "any", "one", "two", "out",
    "pleas", "alway", "never", "usuall", "same", "again", "back", "now", "note",
    "just", "also", "here", "there", "what", "when", "where", "how", "who",
    "does", "did", "get", "got", "make", "made", "take", "took", "last", "time",
    "certain", "certainl", "know", "based", "good", "evening", "hello", "thank",
}


def _stem(tok: str) -> str:
    """Crude suffix stripper so the mock backend bridges morphology the way
    real embeddings bridge it semantically (allergy/allergic, morning/mornings).
    Runs to a fixpoint so 'mornings' and 'morning' both land on 'morn'."""
    changed = True
    while changed:
        changed = False
        for suf in _SUFFIXES:
            if tok.endswith(suf) and len(tok) - len(suf) >= 4:
                tok = tok[: -len(suf)]
                changed = True
                break
    return tok


def _tokens(text: str) -> list[str]:
    out = [_stem(t) for t in _TOKEN.findall(text.lower())]
    return [t for t in out if t not in _STOPWORDS]


def _normalize(vec: list[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / n for x in vec]


class QwenClient:
    """Qwen Cloud via the OpenAI-compatible wire protocol, over httpx."""

    def __init__(self):
        if not settings.qwen_api_key:
            raise RuntimeError("QWEN_API_KEY not set — add it to .env or use LLM_BACKEND=mock")
        self._http = httpx.Client(
            base_url=settings.qwen_base_url,
            headers={"Authorization": f"Bearer {settings.qwen_api_key}"},
            timeout=180.0,
        )

    def _post(self, path: str, body: dict) -> dict:
        """POST with retry + exponential backoff on transient timeouts and
        overload/ratelimit responses. Raises on the final attempt or on a
        non-retryable status (e.g. 400/401/403)."""
        last_exc: Exception | None = None
        for attempt in range(_MAX_ATTEMPTS):
            try:
                r = self._http.post(path, json=body)
                r.raise_for_status()
                return r.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code not in _RETRY_STATUS or attempt == _MAX_ATTEMPTS - 1:
                    raise
                last_exc = e
            except (httpx.TimeoutException, httpx.TransportError) as e:
                if attempt == _MAX_ATTEMPTS - 1:
                    raise
                last_exc = e
            time.sleep(2.0 * (attempt + 1))  # 2s, 4s, 6s
        raise last_exc  # unreachable, but keeps the type checker honest

    def chat(self, system: str, user: str, model: str | None = None,
             json_mode: bool = False) -> str:
        body = {
            "model": model or settings.chat_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        return self._post("/chat/completions", body)["choices"][0]["message"]["content"]

    def embed(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for i in range(0, len(texts), 10):  # DashScope embedding batch limit
            data = self._post("/embeddings", {
                "model": settings.embed_model,
                "input": texts[i:i + 10],
                "dimensions": settings.embed_dim,
            })["data"]
            data = sorted(data, key=lambda d: d["index"])
            out.extend(_normalize(d["embedding"]) for d in data)
        return out


class MockClient:
    """Deterministic offline backend.

    chat(): recognizes the pipeline's prompt kinds by marker tags the callers
    embed in their system prompts ([extract] / [contradiction] / [concierge] /
    [quizjudge]) and produces rule-based outputs good enough to exercise every
    code path. embed(): bag-of-hashed-tokens vectors (token overlap ~= cosine
    similarity), same approach validated in NexusVenue.
    """

    def chat(self, system: str, user: str, model: str | None = None,
             json_mode: bool = False) -> str:
        if "[extract]" in system:
            # Emit one ATOMIC memory per guest sentence that carries a durable
            # signal (the real extraction prompt asks Qwen for exactly this:
            # guest statements only, one standalone fact per memory).
            keywords = ("prefer", "allerg", "always", "never", "love", "hate",
                        "usually", "usual", "need", "morning", "each",
                        "instead", "no longer", "vegetarian", "vegan", "kosher", "halal")
            memories = []
            for line in user.splitlines():
                line = line.strip()
                if not line.lower().startswith("guest:"):
                    continue
                line = line.split(":", 1)[-1].strip()
                for sentence in re.split(r"(?<=[.!?])\s+", line):
                    sentence = sentence.strip().rstrip(".!?")
                    if sentence and any(k in sentence.lower() for k in keywords):
                        memories.append({
                            "content": sentence,
                            "kind": "preference",
                            "importance": 4,
                        })
            return json.dumps({"memories": memories})
        if "[contradiction]" in system:
            # Contradiction = shared topic AND an explicit change: either a
            # negation-polarity flip ("always X" -> "never X") or a change
            # signal in the NEW statement ("instead", "no longer", ...).
            # Mirrors the real prompt: preference CHANGES contradict;
            # compatible or restated facts do not.
            m = re.findall(r'"([^"]+)"', user)
            if len(m) >= 2:
                old, new = m[0], m[1]
                a, b = set(_tokens(old)), set(_tokens(new))
                neg = re.compile(r"\b(never|no longer|not|stopped|given up|quit)\b")
                change = re.compile(r"\b(instead|no longer|switch\w*|chang\w*|quit|given up|stopped|correction)\b")
                polarity_flip = bool(neg.search(old.lower())) != bool(neg.search(new.lower()))
                shared_topic = len(a & b) >= 2
                return json.dumps({"contradicts": shared_topic and
                                   (polarity_flip or bool(change.search(new.lower())))})
            return json.dumps({"contradicts": False})
        if "[quizjudge]" in system:
            m = re.findall(r'"([^"]*)"', user)
            if len(m) >= 2:
                expect = set(_tokens(m[-2]))
                answer = set(_tokens(m[-1]))
                ok = bool(expect) and len(expect & answer) / len(expect) >= 0.5
                return json.dumps({"correct": ok})
            return json.dumps({"correct": False})
        # [concierge] and everything else: answer grounded in provided memories
        # (the memory block lives in the system prompt).
        mems = re.findall(r"- (.+)", system + "\n" + user)
        mems = [m for m in mems if "no prior memories" not in m]
        if mems:
            # Commit to the top-ranked memories, as a real model would.
            return "Certainly. Based on what I know: " + "; ".join(mems[:2]) + "."
        return "Certainly — how may I assist you today?"

    def embed(self, texts: list[str]) -> list[list[float]]:
        out = []
        for text in texts:
            vec = [0.0] * settings.embed_dim
            for tok in _tokens(text):
                h = int.from_bytes(hashlib.sha256(tok.encode()).digest()[:8], "big")
                vec[h % settings.embed_dim] += 1.0
            out.append(_normalize(vec))
        return out


def get_client():
    if settings.llm_backend == "mock":
        return MockClient()
    return QwenClient()


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))
