import { useMutation } from "@tanstack/react-query";
import { evaluationApi } from "@/api/evaluation";
import type { ApiError } from "@/api/client";
import type { RetrievalEvalReport } from "@/types/api";

export function useRetrievalEvalMutation() {
  return useMutation<RetrievalEvalReport, ApiError, void>({
    mutationFn: () => evaluationApi.retrieval(),
    retry: false,
  });
}
