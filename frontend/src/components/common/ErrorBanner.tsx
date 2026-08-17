import { CircleAlert } from "lucide-react";
import { Link } from "react-router-dom";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import type { ApiError } from "@/api/client";

export default function ErrorBanner({ error }: { error: ApiError }) {
  const isNotReady = error.status === 503;
  const isBackendFailure = error.status === 502;

  return (
    <Alert className="border-destructive/30 bg-destructive/10">
      <CircleAlert className="size-4 text-destructive" />
      <AlertTitle className="font-heading text-destructive">
        {isNotReady ? "Corpus not ready" : isBackendFailure ? "AI backend error" : "Request failed"}
      </AlertTitle>
      <AlertDescription className="text-destructive/90">
        {error.detail}
        {isNotReady ? (
          <Button asChild variant="link" className="h-auto p-0 pl-1 text-destructive underline">
            <Link to="/ingest">Ingest the guidelines →</Link>
          </Button>
        ) : null}
      </AlertDescription>
    </Alert>
  );
}
