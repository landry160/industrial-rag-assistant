const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const UNREACHABLE = "Le service ne répond pas. Vérifiez qu'il est démarré, puis réessayez.";

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_URL}${path}`, options);
  } catch {
    throw new Error(UNREACHABLE);
  }
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = typeof data?.detail === "string" ? data.detail : null;
    const error = new Error(detail || "Une erreur est survenue. Réessayez.");
    error.status = response.status;
    throw error;
  }
  return data;
}

const adminHeaders = (token) => (token ? { "X-Admin-Token": token } : {});

export const getConfig = () => request("/config");

export const getDocuments = async () => (await request("/documents")).documents;

export const askQuestion = (question) =>
  request("/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });

export function uploadDocument(file, token) {
  const body = new FormData();
  body.append("file", file);
  return request("/ingest", { method: "POST", body, headers: adminHeaders(token) });
}

export const loadSample = (token) =>
  request("/ingest/sample", { method: "POST", headers: adminHeaders(token) });

export const deleteDocument = (id, token) =>
  request(`/documents/${id}`, { method: "DELETE", headers: adminHeaders(token) });
