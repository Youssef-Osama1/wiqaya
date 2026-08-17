import { useMutation } from "@tanstack/react-query";
import { dataApi, type IngestRequest } from "@/api/data";
import type { ApiError } from "@/api/client";
import type { IngestResponse } from "@/types/api";

export function useIngestMutation() {
  return useMutation<IngestResponse, ApiError, IngestRequest>({
    mutationFn: dataApi.ingest,
    retry: false,
  });
}
