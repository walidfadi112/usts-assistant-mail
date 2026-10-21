import type { Email, Summary } from "../types/email";

const API = "/api";

async function request<T>(path: string, token: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      ...init.headers,
    },
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || `Erreur API (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export async function login(email: string, password: string) {
  const body = new URLSearchParams({ username: email, password });
  const response = await fetch(`${API}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || "Connexion impossible");
  }
  return response.json() as Promise<{ access_token: string; token_type: string }>;
}

export function getEmails(token: string, filters: Record<string, string>, page: number) {
  const params = new URLSearchParams({ page: String(page), page_size: "20" });
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  return request<{ items: Email[]; total: number; page: number; total_pages: number }>(
    `/emails?${params}`, token
  );
}

export function getEmail(token: string, id: number) {
  return request<Email>(`/emails/${id}`, token);
}

export function updateEmail(token: string, id: number, data: Partial<Email>) {
  return request<Email>(`/emails/${id}`, token, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function getSummary(token: string) {
  return request<Summary>("/summary/today", token);
}

export function classifyEmail(token: string, id: number) {
  return request<Email>(`/emails/${id}/classify`, token, { method: "POST" });
}
