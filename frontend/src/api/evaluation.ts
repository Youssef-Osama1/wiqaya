import { apiClient } from "./client";
import type { E2EEvalReport, RetrievalEvalReport, RetrievalMode } from "@/types/api";

export interface E2EEvalParams {
  mode?: RetrievalMode;
  k?: number;
}

export const evaluationApi = {
  retrieval: () => apiClient.post<RetrievalEvalReport>("/evaluation/retrieval"),
  latestRetrieval: () => apiClient.get<RetrievalEvalReport>("/evaluation/retrieval/latest"),
  latestE2E: () => apiClient.get<E2EEvalReport>("/evaluation/e2e/latest"),
  e2e: (params: E2EEvalParams = {}) => {
    const search = new URLSearchParams();
    if (params.mode) search.set("mode", params.mode);
    if (params.k !== undefined) search.set("k", String(params.k));
    const query = search.toString();
    return apiClient.post<E2EEvalReport>(`/evaluation/e2e${query ? `?${query}` : ""}`);
  },
};
