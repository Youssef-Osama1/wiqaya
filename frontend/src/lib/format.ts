import type { ChunkMetadata, RetrievalMode } from "@/types/api";

export function sectionBreadcrumb(meta: ChunkMetadata): string {
  return meta.section_path.length > 0 ? meta.section_path.join(" › ") : meta.section_title;
}

export function pageRange(meta: ChunkMetadata): string {
  return meta.page_end && meta.page_end !== meta.page_number
    ? `p.${meta.page_number}–${meta.page_end}`
    : `p.${meta.page_number}`;
}

interface ScoreDisplay {
  label: string;
  showBar: boolean;
  barValue: number;
}

export function formatScore(score: number, mode: RetrievalMode): ScoreDisplay {
  if (mode === "bm25") {
    return { label: score.toFixed(2), showBar: false, barValue: 0 };
  }
  return { label: score.toFixed(3), showBar: score >= 0 && score <= 1, barValue: Math.max(0, Math.min(1, score)) * 100 };
}

export function formatTimestamp(iso: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(iso));
}

export function formatMs(ms: number): string {
  return ms < 1000 ? `${ms.toFixed(0)}ms` : `${(ms / 1000).toFixed(2)}s`;
}

export function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

const DOC_STRIPE_CLASSES: Record<string, string> = {
  who_hypertension: "border-l-chart-4",
  nice_ng136: "border-l-chart-1",
};

export function docStripeClass(docKey: string): string {
  return DOC_STRIPE_CLASSES[docKey] ?? "border-l-chart-5";
}

export function stripMarkdown(text: string): string {
  return text
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1")
    .replace(/^\s{0,3}#{1,6}\s+/gm, "")
    .replace(/^\s{0,3}>\s?/gm, "")
    .replace(/^\s{0,3}[-*+]\s+/gm, "")
    .replace(/\*\*\*(.+?)\*\*\*/g, "$1")
    .replace(/\*\*(.+?)\*\*/g, "$1")
    .replace(/\*(.+?)\*/g, "$1")
    // underscores only count as emphasis at word boundaries -- CommonMark treats
    // intra-word ones as literal, and identifiers like who_hypertension_p028 rely on that.
    .replace(/(?<![A-Za-z0-9])___(.+?)___(?![A-Za-z0-9])/g, "$1")
    .replace(/(?<![A-Za-z0-9])__(.+?)__(?![A-Za-z0-9])/g, "$1")
    .replace(/(?<![A-Za-z0-9])_(.+?)_(?![A-Za-z0-9])/g, "$1")
    .replace(/\s+/g, " ")
    .trim();
}
