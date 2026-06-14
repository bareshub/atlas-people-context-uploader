// All network calls live here so components only deal with typed data.

export interface InferredMetadata {
  title: string;
  summary: string;
  document_type: string;
  time_period: string;
  refers_to: string[];
  key_topics: string[];
}

export interface Document {
  id: string;
  filename: string;
  content_key: string;
  size_bytes: number;
  uploaded_at: string;
  updated_at: string;
  metadata: InferredMetadata;
}

// Same-origin by default; nginx (prod) and Vite (dev) both proxy "/api".
const BASE_URL = import.meta.env.VITE_API_BASE ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, init);
  if (!response.ok) {
    const detail = await response
      .json()
      .then((body) => body.detail as string)
      .catch(() => response.statusText);
    throw new Error(detail || "Request failed");
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export function listDocuments(): Promise<Document[]> {
  return request<Document[]>("/api/documents");
}

export function uploadDocument(file: File): Promise<Document> {
  const form = new FormData();
  form.append("file", file);
  return request<Document>("/api/documents", { method: "POST", body: form });
}

export function updateMetadata(
  id: string,
  metadata: InferredMetadata,
): Promise<Document> {
  return request<Document>(`/api/documents/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(metadata),
  });
}

export function reinferMetadata(id: string): Promise<Document> {
  return request<Document>(`/api/documents/${id}/reinfer`, { method: "POST" });
}

export function deleteDocument(id: string): Promise<void> {
  return request<void>(`/api/documents/${id}`, { method: "DELETE" });
}
