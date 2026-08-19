import { useQuery } from "@tanstack/react-query";
import { evaluationApi } from "@/api/evaluation";
import { ApiError } from "@/api/client";
import type { E2EEvalReport, RetrievalEvalReport } from "@/types/api";

export const LATEST_E2E_KEY = ["evaluation", "e2e", "latest"];
export const LATEST_RETRIEVAL_KEY = ["evaluation", "retrieval", "latest"];

// a 404 means "nothing has been run yet", which is a normal empty state rather than a
// failure — retrying it just delays the empty state the dashboard already knows how to show.
function isMissingReport(error: unknown) {
  return error instanceof ApiError && error.status === 404;
}

export function useLatestE2EEval() {
  return useQuery<E2EEvalReport, ApiError>({
    queryKey: LATEST_E2E_KEY,
    queryFn: () => evaluationApi.latestE2E(),
    retry: (_count, error) => !isMissingReport(error),
    staleTime: Infinity,
  });
}

export function useLatestRetrievalEval() {
  return useQuery<RetrievalEvalReport, ApiError>({
    queryKey: LATEST_RETRIEVAL_KEY,
    queryFn: () => evaluationApi.latestRetrieval(),
    retry: (_count, error) => !isMissingReport(error),
    staleTime: Infinity,
  });
}
