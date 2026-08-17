import { useQuery } from "@tanstack/react-query";

interface HealthResponse {
  app: string;
  status: string;
}

const API_ROOT = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1").replace(/\/api\/v1\/?$/, "");

async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(API_ROOT);
  if (!res.ok) throw new Error(`API unreachable (${res.status})`);
  return res.json() as Promise<HealthResponse>;
}

export function useHealthCheck() {
  return useQuery<HealthResponse>({
    queryKey: ["health"],
    queryFn: fetchHealth,
    refetchInterval: 30_000,
    retry: false,
  });
}
