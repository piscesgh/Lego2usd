import type { AssemblyState, PartDefinition, PartSummary, PreviewResponse } from "./types";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(payload.detail ?? "Request failed");
  }
  return response.json() as Promise<T>;
}

export async function searchParts(query: string): Promise<PartSummary[]> {
  const response = await fetch(`${API_BASE}/api/parts?query=${encodeURIComponent(query)}`);
  return parseJson<PartSummary[]>(response);
}

export async function getPart(sku: string): Promise<PartDefinition> {
  const response = await fetch(`${API_BASE}/api/parts/${encodeURIComponent(sku)}`);
  return parseJson<PartDefinition>(response);
}

export async function previewConnection(payload: {
  assembly: AssemblyState;
  source_instance_id: string;
  source_port_id: string;
  target_sku: string;
  target_port_id: string;
}): Promise<PreviewResponse> {
  const response = await fetch(`${API_BASE}/api/assemblies/preview-connection`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseJson<PreviewResponse>(response);
}

export async function connectPart(payload: {
  assembly: AssemblyState;
  target_sku: string;
  source_instance_id?: string;
  source_port_id?: string;
  target_port_id?: string;
}): Promise<AssemblyState> {
  const response = await fetch(`${API_BASE}/api/assemblies/connect`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseJson<AssemblyState>(response);
}

export async function exportUsd(assembly: AssemblyState): Promise<string> {
  const response = await fetch(`${API_BASE}/api/assemblies/export/usd`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ assembly }),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(payload.detail ?? "Export failed");
  }
  return response.text();
}

