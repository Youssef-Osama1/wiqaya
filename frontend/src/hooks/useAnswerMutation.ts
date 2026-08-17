import { useMutation } from "@tanstack/react-query";
import type { ApiError } from "@/api/client";
import { nlpApi, type AskRequest } from "@/api/nlp";
import type { AnswerTrace } from "@/types/api";

export function useAnswerMutation() {
  return useMutation<AnswerTrace, ApiError, AskRequest>({
    mutationFn: nlpApi.answer,
    retry: 1,
  });
}
