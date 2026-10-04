"use client";

import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function onAsk(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Request failed");
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ maxWidth: 720, margin: "4rem auto", padding: "0 1rem" }}>
      <h1>Industrial RAG Assistant</h1>
      <p>Ask a technical question — answers come from your plant documentation, with sources.</p>
      <form onSubmit={onAsk} style={{ display: "flex", gap: "0.5rem" }}>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. What is the torque spec for pump P-101?"
          style={{ flex: 1, padding: "0.6rem" }}
        />
        <button type="submit" disabled={loading || !question.trim()}>
          {loading ? "…" : "Ask"}
        </button>
      </form>
      {error && <p style={{ color: "crimson" }}>Error: {error}</p>}
      {result && (
        <section style={{ marginTop: "2rem" }}>
          <h2>Answer</h2>
          <p>{result.answer}</p>
          <h3>Sources</h3>
          <ul>
            {result.sources.map((s, i) => (
              <li key={i}>
                {s.document} — {s.section} (score {s.score.toFixed(2)})
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}
