/* ──────────────────────────────────────────────────
   API helper functions for the speaker recognition backend
   ────────────────────────────────────────────────── */

import type {
  AnalyzeResponse,
  RegisterResponse,
  SpeakerListResponse,
  HealthResponse,
} from "@/types/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(body.detail || "Request failed", res.status);
  }
  return res.json();
}

/** GET /health */
export async function checkHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`);
  return handleResponse<HealthResponse>(res);
}

/** POST /api/v1/analyze/ */
export async function analyzeAudio(
  file: File | Blob,
  options?: { threshold?: number; chunkDuration?: number }
): Promise<AnalyzeResponse> {
  const form = new FormData();
  form.append("file", file, file instanceof File ? file.name : "recording.wav");

  let url = `${API_BASE}/api/v1/analyze/`;
  const params = new URLSearchParams();
  if (options?.threshold !== undefined) params.set("threshold", String(options.threshold));
  if (options?.chunkDuration !== undefined) params.set("chunk_duration", String(options.chunkDuration));
  if (params.toString()) url += `?${params}`;

  const res = await fetch(url, { method: "POST", body: form });
  return handleResponse<AnalyzeResponse>(res);
}

/** POST /api/v1/speakers/register */
export async function registerSpeaker(
  name: string,
  files: (File | Blob)[]
): Promise<RegisterResponse> {
  const form = new FormData();
  form.append("speaker_name", name);
  files.forEach((f, i) => {
    form.append("files", f, f instanceof File ? f.name : `sample_${i}.wav`);
  });

  const res = await fetch(`${API_BASE}/api/v1/speakers/register`, {
    method: "POST",
    body: form,
  });
  return handleResponse<RegisterResponse>(res);
}

/** GET /api/v1/speakers/ */
export async function listSpeakers(): Promise<SpeakerListResponse> {
  const res = await fetch(`${API_BASE}/api/v1/speakers/`);
  return handleResponse<SpeakerListResponse>(res);
}

export { ApiError };
