import { Suspense } from "react";
import { Outlet } from "react-router-dom";
import Header from "@/components/layout/Header";
import DisclaimerFooter from "@/components/layout/DisclaimerFooter";
import { Skeleton } from "@/components/ui/skeleton";

function PageFallback() {
  return (
    <div className="space-y-4 p-6">
      <Skeleton className="h-8 w-48" />
      <Skeleton className="h-32 w-full" />
      <Skeleton className="h-32 w-full" />
    </div>
  );
}

export default function AppShell() {
  return (
    <div className="flex min-h-svh w-full flex-col">
      <Header />
      <main className="mx-auto w-full max-w-[1440px] flex-1 px-6">
        <Suspense fallback={<PageFallback />}>
          <Outlet />
        </Suspense>
      </main>
      <DisclaimerFooter />
    </div>
  );
}
