import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from dealjudge.client import DeciderClient, DeciderResult, DeciderUnavailable
from dealjudge.levels import LEVELS
from dealjudge.questions import decider_questions


def serve(status, body):
    """A one-shot fake Decider server; returns (url, requests_seen)."""
    seen = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            seen.append(json.loads(self.rfile.read(int(self.headers["content-length"]))))
            payload = body if isinstance(body, bytes) else json.dumps(body).encode()
            self.send_response(status)
            self.send_header("content-type", "application/json")
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{server.server_port}", seen


def test_ask_returns_answers_and_latency_and_sends_the_wire_shape():
    url, seen = serve(200, {"answers": {"is_real": {"noul": 0.9}}, "latency_ms": 12.5})
    result = DeciderClient(url).ask("estado", {"is_real": {"type": "noul"}})
    assert result == DeciderResult(answers={"is_real": {"noul": 0.9}}, latency_ms=12.5)
    assert seen == [{"state": "estado", "questions": {"is_real": {"type": "noul"}}}]


def test_http_error_raises_decider_unavailable():
    url, _ = serve(500, b"boom")
    with pytest.raises(DeciderUnavailable):
        DeciderClient(url).ask("estado", {})


def test_connection_refused_raises_decider_unavailable():
    with pytest.raises(DeciderUnavailable):
        DeciderClient("http://127.0.0.1:9", timeout=2).ask("estado", {})


def test_payload_without_answers_raises_decider_unavailable():
    url, _ = serve(200, {"nope": 1})
    with pytest.raises(DeciderUnavailable):
        DeciderClient(url).ask("estado", {})


def test_questions_have_the_three_typed_keys():
    q = decider_questions()
    assert set(q) == {"is_real", "level", "fits_user"}
    assert q["is_real"]["type"] == "noul"
    assert q["fits_user"]["type"] == "noul"
    assert q["level"]["type"] == "choice"
    assert tuple(q["level"]["criteria"]) == LEVELS
