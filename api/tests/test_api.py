import pytest

from app import config, main
from app.ratelimit import RateLimiter
from app.retrieval import extract_codes, retrieve, rrf_merge, search
from tests.test_parsing import make_pdf


def upload(client, name, data, headers=None):
    return client.post("/ingest", files={"file": (name, data)}, headers=headers or {})


def test_health_keeps_its_contract(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_ask_on_an_empty_database_abstains(client):
    body = client.post("/ask", json={"question": "Quelle graisse utiliser ?"}).json()
    assert body["grounded"] is False
    assert body["sources"] == []
    assert "Je ne trouve pas" in body["answer"]


def test_upload_txt_then_list_then_delete(client):
    response = upload(client, "procedure.txt", "Vidanger la pompe P-7 chaque mois.".encode())
    assert response.status_code == 200
    assert response.json()["chunks_indexed"] == 1

    documents = client.get("/documents").json()["documents"]
    assert [d["source"] for d in documents] == ["procedure.txt"]
    assert documents[0]["needs_reindex"] is False

    assert client.delete(f"/documents/{documents[0]['id']}").json() == {"deleted": True}
    assert client.get("/documents").json()["documents"] == []
    assert client.delete(f"/documents/{documents[0]['id']}").status_code == 404


def test_upload_pdf_keeps_the_page_in_sources(client):
    pdf = make_pdf(["Introduction generale.", "La pompe P-7 se vidange chaque mois."])
    assert upload(client, "manuel.pdf", pdf).status_code == 200
    body = client.post("/ask", json={"question": "vidange pompe P-7"}).json()
    assert body["sources"][0]["document"] == "manuel.pdf"
    assert body["sources"][0]["page"] == 2


def test_same_file_is_not_indexed_twice(client):
    assert upload(client, "a.txt", b"Contenu du manuel.").json()["status"] == "created"
    second = upload(client, "a.txt", b"Contenu du manuel.").json()
    assert second == {"chunks_indexed": 0, "source": "a.txt", "status": "unchanged"}
    assert len(client.get("/documents").json()["documents"]) == 1


def test_a_new_version_replaces_the_old_chunks(client):
    upload(client, "a.txt", b"Ancienne valeur : 10 bars.")
    assert upload(client, "a.txt", b"Nouvelle valeur : 12 bars.").json()["status"] == "updated"
    contents = [h.content for h in search("valeur bars")]
    assert contents == ["Nouvelle valeur : 12 bars."]


def test_path_in_a_filename_is_ignored(client):
    assert upload(client, "../../etc/passwd.txt", b"texte").json()["source"] == "passwd.txt"


@pytest.mark.parametrize(
    ("name", "data", "expected"),
    [("a.exe", b"x", 422), ("vide.txt", b"", 422), ("casse.pdf", b"nope", 422)],
)
def test_bad_uploads_get_a_clear_error(client, name, data, expected):
    response = upload(client, name, data)
    assert response.status_code == expected
    assert "Traceback" not in response.text


def test_upload_size_limit(client, monkeypatch):
    monkeypatch.setattr(config, "MAX_UPLOAD_MB", 1)
    response = upload(client, "gros.txt", b"x" * (1024 * 1024 + 1))
    assert response.status_code == 413


@pytest.mark.parametrize("question", ["", "  ", "ab", "x" * 1001])
def test_invalid_questions_are_refused(client, question):
    assert client.post("/ask", json={"question": question}).status_code == 422


def test_extractive_mode_works_without_any_key(client, sample):
    body = client.post(
        "/ask", json={"question": "référence pièce sonde T88-PROBE-02"}
    ).json()
    assert body["mode"] == "extractive"
    assert body["grounded"] is True
    assert body["sources"][0]["document"] == "depannage-capteur-T88.txt"
    assert "[1]" in body["answer"]


def test_code_written_differently_still_matches(client, sample):
    hits = retrieve("capteur T88", min_score=0.99)
    assert hits and all(h.exact_code for h in hits)
    assert hits[0].document == "depannage-capteur-T88.txt"


def test_unrelated_question_is_rejected_by_the_threshold(client, sample):
    assert retrieve("recette tarte pommes", min_score=0.5) == []


def test_extract_codes():
    assert extract_codes("capteur T-88 et pièce T88-PROBE-02 ?") == ["T88", "T88PROBE02"]
    assert extract_codes("la courroie du convoyeur") == []


def test_rrf_rewards_presence_in_several_rankings():
    scores = rrf_merge([[1, 2], [2, 3]])
    assert max(scores, key=scores.get) == 2


def test_write_routes_require_the_token_when_set(client, monkeypatch):
    monkeypatch.setattr(config, "ADMIN_TOKEN", "secret")
    assert upload(client, "a.txt", b"x").status_code == 401
    assert upload(client, "a.txt", b"x", {"X-Admin-Token": "faux"}).status_code == 401
    assert client.post("/ingest/sample").status_code == 401
    assert client.delete("/documents/1").status_code == 401
    assert upload(client, "a.txt", b"texte", {"X-Admin-Token": "secret"}).status_code == 200
    assert client.get("/config").json()["writes_protected"] is True


def test_rate_limit(client, monkeypatch):
    monkeypatch.setattr(main, "limiter", RateLimiter(2))
    statuses = [
        client.post("/ask", json={"question": "abc"}).status_code for _ in range(3)
    ]
    assert statuses == [200, 200, 429]


def test_cors_preflight_from_the_web_ui(client):
    response = client.options(
        "/ask",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_other_origins_are_not_allowed(client):
    response = client.options(
        "/ask",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in response.headers


def test_config_exposes_no_secret(client):
    assert client.get("/config").json()["provider"] == "extractive"
    assert "key" not in client.get("/config").text.lower()


def test_old_style_database_url_is_accepted():
    assert (
        config._normalize_database_url("postgresql+psycopg://u:p@db:5432/x")
        == "postgresql://u:p@db:5432/x"
    )


def test_evaluation_runs_end_to_end(client):
    from eval.evaluate import evaluate, sweep

    main.ingest_sample()
    report = evaluate()
    assert 0 <= report.mrr <= 1
    assert len(sweep(report)) == 8
