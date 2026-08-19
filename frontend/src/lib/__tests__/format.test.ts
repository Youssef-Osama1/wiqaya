import { describe, expect, it } from "vitest";
import { formatMs, formatPercent, formatScore, pageRange, sectionBreadcrumb, stripMarkdown } from "@/lib/format";
import type { ChunkMetadata } from "@/types/api";

const baseMeta: ChunkMetadata = {
  document_name: "NICE NG136",
  page_number: 14,
  section_title: "Monitoring",
  chunk_id: "nice_ng136-p014-abc",
  source_url: "https://nice.org.uk/ng136",
  doc_key: "nice_ng136",
  section_path: ["Recommendations", "Monitoring"],
  page_end: null,
  token_count: 100,
  recommendation_ids: [],
  has_cross_reference: false,
  printed_page: null,
};

describe("sectionBreadcrumb", () => {
  it("joins section_path with a chevron", () => {
    expect(sectionBreadcrumb(baseMeta)).toBe("Recommendations › Monitoring");
  });

  it("falls back to section_title when section_path is empty", () => {
    expect(sectionBreadcrumb({ ...baseMeta, section_path: [] })).toBe("Monitoring");
  });
});

describe("pageRange", () => {
  it("shows a single page when page_end is null", () => {
    expect(pageRange(baseMeta)).toBe("p.14");
  });

  it("shows a range when page_end differs from page_number", () => {
    expect(pageRange({ ...baseMeta, page_end: 16 })).toBe("p.14–16");
  });

  it("shows a single page when page_end equals page_number", () => {
    expect(pageRange({ ...baseMeta, page_end: 14 })).toBe("p.14");
  });
});

describe("formatScore", () => {
  it("formats bm25 scores without a bar, since bm25's scale is unbounded", () => {
    const result = formatScore(12.345, "bm25");
    expect(result.label).toBe("12.35");
    expect(result.showBar).toBe(false);
  });

  it("formats hybrid_rerank scores with a bar when in 0..1", () => {
    const result = formatScore(0.938, "hybrid_rerank");
    expect(result.label).toBe("0.938");
    expect(result.showBar).toBe(true);
    expect(result.barValue).toBeCloseTo(93.8);
  });

  it("does not show a bar for an out-of-range semantic score", () => {
    const result = formatScore(1.5, "semantic");
    expect(result.showBar).toBe(false);
  });
});

describe("formatMs", () => {
  it("shows milliseconds under 1000ms", () => {
    expect(formatMs(450)).toBe("450ms");
  });

  it("shows seconds at or above 1000ms", () => {
    expect(formatMs(4200)).toBe("4.20s");
  });
});

describe("formatPercent", () => {
  it("formats a 0..1 fraction as a percentage string", () => {
    expect(formatPercent(0.2222)).toBe("22.2%");
  });
});

describe("stripMarkdown", () => {
  it("removes emphasis markers but keeps the words", () => {
    expect(stripMarkdown("Reduce BP to **150/90 mmHg** for *most* adults.")).toBe(
      "Reduce BP to 150/90 mmHg for most adults.",
    );
  });

  it("leaves intra-word underscores alone, so chunk ids survive being read aloud", () => {
    expect(stripMarkdown("See who_hypertension_p028 and nice_ng136 for detail.")).toBe(
      "See who_hypertension_p028 and nice_ng136 for detail.",
    );
  });

  it("leaves an unformatted clinical recommendation byte-identical", () => {
    const prose =
      "For adults under 80, the clinic blood pressure target is below 140/90 mmHg, while for those aged 80 and over, it is below 150/90 mmHg (HBPM/ABPM targets are lower).";
    expect(stripMarkdown(prose)).toBe(prose);
  });
});
