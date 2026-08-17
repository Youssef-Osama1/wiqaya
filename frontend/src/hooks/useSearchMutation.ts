import { useMutation } from "@tanstack/react-query";
import type { ApiError } from "@/api/client";
import { nlpApi, type AskRequest } from "@/api/nlp";
import type { RetrievalResult } from "@/types/api";

export function useSearchMutation() {
  return useMutation<RetrievalResult, ApiError, AskRequest>({
    mutationFn: nlpApi.search,
    retry: 1,
  });
}
