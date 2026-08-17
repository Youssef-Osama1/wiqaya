import { apiClient } from "./client";
import type { AnswerTrace, RetrievalMode, RetrievalResult } from "@/types/api";

export interface AskRequest {
  query: string;
  mode?: RetrievalMode;
  k?: number;
}

export const nlpApi = {
  search: (body: AskRequest) => apiClient.post<RetrievalResult>("/nlp/search", body),
  answer: (body: AskRequest) => apiClient.post<AnswerTrace>("/nlp/answer", body),
};
