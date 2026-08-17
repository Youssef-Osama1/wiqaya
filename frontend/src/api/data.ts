import { apiClient } from "./client";
import type { IngestResponse } from "@/types/api";

export interface IngestRequest {
  doc_keys?: string[];
  target_tokens?: number;
  hard_max_tokens?: number;
  min_tokens?: number;
  overlap_tokens?: number;
}

export const dataApi = {
  ingest: (body: IngestRequest = {}) => apiClient.post<IngestResponse>("/data/ingest", body),
};
