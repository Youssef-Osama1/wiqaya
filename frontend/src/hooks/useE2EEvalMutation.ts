import { useMutation } from "@tanstack/react-query";
import { evaluationApi, type E2EEvalParams } from "@/api/evaluation";
import type { ApiError } from "@/api/client";
import type { E2EEvalReport } from "@/types/api";

export function useE2EEvalMutation() {
  return useMutation<E2EEvalReport, ApiError, E2EEvalParams>({
    mutationFn: (params) => evaluationApi.e2e(params),
    retry: false,
  });
}
