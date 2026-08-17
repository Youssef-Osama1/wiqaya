import { lazy } from "react";
import { Route, Routes } from "react-router-dom";
import AppShell from "@/components/layout/AppShell";

const AskPage = lazy(() => import("@/pages/AskPage"));
const SearchPage = lazy(() => import("@/pages/SearchPage"));
const DashboardPage = lazy(() => import("@/pages/DashboardPage"));
const IngestPage = lazy(() => import("@/pages/IngestPage"));
const AboutPage = lazy(() => import("@/pages/AboutPage"));
const NotFoundPage = lazy(() => import("@/pages/NotFoundPage"));

export default function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/*" element={<AskPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/ingest" element={<IngestPage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
