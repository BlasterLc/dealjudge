"""Synchronous HTTP client for a running Strands Decider server (urllib only).

Wire shape: POST ``/v1/systemone`` with ``{"state", "questions"}``; answers come back under
the same keys. Same shape as the sponsor's example client.
"""

import json
import os
import urllib.error
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

ENV_URL = "DEALJUDGE_DECIDER_URL"
DEFAULT_URL = "http://127.0.0.1:8000"
SERVE_HINT = "strands-decider serve StrandsAgents/strands-decider-2B-hobson-v19 --port 8000"


class DeciderUnavailable(RuntimeError):
    """The Decider server did not give a usable answer."""


@dataclass(frozen=True)
class DeciderResult:
    answers: dict[str, Any]
    latency_ms: float | None = None


class DeciderClient:
    def __init__(self, url: str | None = None, timeout: float = 120.0) -> None:
        self.url = (url or os.environ.get(ENV_URL, DEFAULT_URL)).rstrip("/")
        self.timeout = timeout

    def ask(self, state: str, questions: Mapping[str, Mapping[str, Any]]) -> DeciderResult:
        body = json.dumps({"state": state, "questions": dict(questions)}, ensure_ascii=False).encode()
        request = urllib.request.Request(
            f"{self.url}/v1/systemone", data=body, headers={"content-type": "application/json"}
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read())
            return DeciderResult(answers=payload["answers"], latency_ms=payload.get("latency_ms"))
        except urllib.error.HTTPError as exc:
            raise DeciderUnavailable(f"Decider at {self.url} answered HTTP {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise DeciderUnavailable(f"no Decider at {self.url} ({exc}). Start one with: {SERVE_HINT}") from exc
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
            raise DeciderUnavailable(f"Decider at {self.url} answered nonsense ({exc})") from exc
