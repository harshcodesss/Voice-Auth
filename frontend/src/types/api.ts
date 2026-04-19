/* ──────────────────────────────────────────────────
   Type definitions matching the FastAPI backend
   ────────────────────────────────────────────────── */

export interface ChunkPrediction {
  chunk_index: number;
  start_sec: number;
  end_sec: number;
  speaker: string;
  similarity: number;
  is_known: boolean;
}

export interface AnalyzeResponse {
  filename: string;
  duration_sec: number;
  final_speaker: string;
  similarity: number;
  is_known: boolean;
  num_chunks: number;
  threshold_used: number;
  chunks: ChunkPrediction[];
}

export interface RegisterResponse {
  speaker_name: string;
  files_processed: number;
  message: string;
}

export interface SpeakerInfo {
  name: string;
  registered_at: string | null;
}

export interface SpeakerListResponse {
  count: number;
  speakers: SpeakerInfo[];
}

export interface HealthResponse {
  status: string;
  speakers_loaded: number;
  model_ready: boolean;
}
