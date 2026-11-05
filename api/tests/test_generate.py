"""Provider logic, and the real google-genai SDK against a local fake Gemini server."""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from app import config, generate
from app.generate import (
    ABSTAIN_MESSAGE,
    NOTICE_LLM_DOWN,
    NOTICE_UNCITED,
    apply_citations,
    generate_answer,
)
from app.retrieval import Hit


def hit(n: int, document: str = "doc.txt") -> Hit:
    return Hit(n, document, None, f"Passage {n}.", 0.8)


HITS = [hit(1, "a.txt"), hit(2, "b.txt"), hit(3, "c.txt")]


@pytest.fixture
def llm(monkeypatch):
    def install(reply):
        def fake(provider, prompt):
            if isinstance(reply, Exception):
                raise reply
            return reply

        monkeypatch.setattr(config, "GEMINI_API_KEY", "cle")
        monkeypatch.setattr(generate, "_call_llm", fake)

    return install


def test_citations_are_renumbered_by_first_use():
    text, cited = apply_citations("Voir [3] puis [1], encore [3].", HITS)
    assert text == "Voir [1] puis [2], encore [1]."
    assert [h.document for h in cited] == ["c.txt", "a.txt"]


def test_invented_citations_are_removed():
    text, cited = apply_citations("Fait réel [2] et fait inventé [9].", HITS)
    assert text == "Fait réel [1] et fait inventé."
    assert [h.document for h in cited] == ["b.txt"]


def test_cited_answer_keeps_only_cited_sources(llm):
    llm("La réponse est 12 bars [2].")
    result = generate_answer("q", HITS)
    assert result.mode == "gemini"
    assert result.grounded is True
    assert result.answer == "La réponse est 12 bars [1]."
    assert [h.document for h in result.hits] == ["b.txt"]


def test_model_abstention_is_honored(llm):
    llm("NON_TROUVE")
    result = generate_answer("q", HITS)
    assert result.answer == ABSTAIN_MESSAGE
    assert result.grounded is False
    assert result.hits == []


def test_uncited_answer_is_never_returned(llm):
    llm("La pression est de 500 bars.")
    result = generate_answer("q", HITS)
    assert "500 bars" not in result.answer
    assert result.mode == "extractive"
    assert result.notice == NOTICE_UNCITED


def test_llm_failure_degrades_to_extracts(llm):
    llm(generate.LLMError("quota"))
    result = generate_answer("q", HITS)
    assert result.mode == "extractive"
    assert result.notice == NOTICE_LLM_DOWN
    assert "[1]" in result.answer


def test_no_passage_means_no_llm_call(llm):
    llm(AssertionError("ne doit pas être appelé"))
    assert generate_answer("q", []).grounded is False


def test_auto_prefers_gemini_then_claude(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "")
    assert generate.active_provider() == "extractive"
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "cle")
    assert generate.active_provider() == "anthropic"
    monkeypatch.setattr(config, "GEMINI_API_KEY", "cle")
    assert generate.active_provider() == "gemini"


def test_prompt_numbers_the_passages():
    prompt = generate.build_user_prompt("Ma question ?", HITS)
    assert '<passage numero="3" document="c.txt">' in prompt
    assert prompt.endswith("Question : Ma question ?")


class FakeGemini(BaseHTTPRequestHandler):
    status = 200
    reply = "La courroie s'inspecte chaque semaine [1]."
    requests: list = []

    def do_POST(self):
        length = int(self.headers["Content-Length"])
        FakeGemini.requests.append(
            {
                "path": self.path,
                "key": self.headers.get("x-goog-api-key"),
                "body": json.loads(self.rfile.read(length)),
            }
        )
        if self.status == 200:
            payload = {
                "candidates": [
                    {"content": {"role": "model", "parts": [{"text": self.reply}]}}
                ]
            }
        else:
            payload = {
                "error": {
                    "code": self.status,
                    "message": "quota",
                    "status": "RESOURCE_EXHAUSTED",
                }
            }
        data = json.dumps(payload).encode()
        self.send_response(self.status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


@pytest.fixture
def gemini_server(monkeypatch):
    server = HTTPServer(("127.0.0.1", 0), FakeGemini)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    FakeGemini.requests = []
    FakeGemini.status = 200
    monkeypatch.setattr(config, "GEMINI_API_KEY", "cle-de-test")
    monkeypatch.setattr(config, "GEMINI_BASE_URL", f"http://127.0.0.1:{server.server_port}")
    generate._gemini_client.cache_clear()
    yield FakeGemini
    server.shutdown()
    generate._gemini_client.cache_clear()


def test_real_sdk_sends_the_expected_request(gemini_server):
    result = generate_answer("À quelle fréquence ?", HITS)
    assert result.mode == "gemini"
    assert result.answer == "La courroie s'inspecte chaque semaine [1]."

    request = gemini_server.requests[0]
    assert request["path"].endswith("/models/gemini-3.8-flash:generateContent")
    assert request["key"] == "cle-de-test"
    assert "NON_TROUVE" in request["body"]["systemInstruction"]["parts"][0]["text"]
    assert "À quelle fréquence ?" in request["body"]["contents"][0]["parts"][0]["text"]


def test_real_sdk_quota_error_degrades_to_extracts(gemini_server):
    gemini_server.status = 429
    result = generate_answer("q", HITS)
    assert result.mode == "extractive"
    assert result.notice == NOTICE_LLM_DOWN


class FakeClaude(BaseHTTPRequestHandler):
    requests: list = []

    def do_POST(self):
        length = int(self.headers["Content-Length"])
        FakeClaude.requests.append(
            {
                "path": self.path,
                "credential": self.headers.get("x-api-key")
                or self.headers.get("authorization"),
                "body": json.loads(self.rfile.read(length)),
            }
        )
        data = json.dumps(
            {
                "id": "msg_test",
                "type": "message",
                "role": "assistant",
                "model": config.ANTHROPIC_MODEL,
                "content": [{"type": "text", "text": "Réponse de Claude [2]."}],
                "stop_reason": "end_turn",
                "stop_sequence": None,
                "usage": {"input_tokens": 1, "output_tokens": 1},
            }
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


def test_real_anthropic_sdk_sends_the_expected_request(monkeypatch):
    server = HTTPServer(("127.0.0.1", 0), FakeClaude)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    FakeClaude.requests = []
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "cle-claude")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", f"http://127.0.0.1:{server.server_port}")
    generate._anthropic_client.cache_clear()
    try:
        result = generate_answer("Question ?", HITS)
    finally:
        server.shutdown()
        generate._anthropic_client.cache_clear()

    assert result.mode == "anthropic"
    assert result.answer == "Réponse de Claude [1]."
    request = FakeClaude.requests[0]
    assert request["path"].endswith("/v1/messages")
    assert "cle-claude" in request["credential"]
    assert request["body"]["model"] == config.ANTHROPIC_MODEL
    assert "NON_TROUVE" in request["body"]["system"]
