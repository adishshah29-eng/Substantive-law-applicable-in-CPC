import type { CitationVerdict, ClaimWithVerdict, SourceChunk } from "./types";

export function sourceLabel(chunk: SourceChunk): string {
  if (chunk.source_type === "judgment") {
    const parts = [chunk.case_name, chunk.citation_string].filter(Boolean);
    return parts.join(", ");
  }
  const parts = [chunk.act_name];
  if (chunk.section_number) parts.push(`Section ${chunk.section_number}`);
  if (chunk.order_number) parts.push(`Order ${chunk.order_number}`);
  if (chunk.rule_number) parts.push(`Rule ${chunk.rule_number}`);
  return parts.filter(Boolean).join(", ");
}

export type FlagTier = "critical" | "review" | "verified";

export type FlagItem =
  | { kind: "claim"; id: string; data: ClaimWithVerdict }
  | { kind: "citation"; id: string; data: CitationVerdict };

export function tierOf(item: FlagItem): FlagTier {
  if (item.kind === "citation") {
    return item.data.verified ? "verified" : "critical";
  }
  switch (item.data.verdict.status) {
    case "supported":
      return "verified";
    case "contradicted":
      return "critical";
    default:
      return "review";
  }
}

export function buildFlagItems(
  claims: ClaimWithVerdict[],
  citationVerdicts: CitationVerdict[]
): FlagItem[] {
  const claimItems: FlagItem[] = claims.map((c) => ({
    kind: "claim",
    id: c.claim.id,
    data: c,
  }));
  const citationItems: FlagItem[] = citationVerdicts.map((cv, i) => ({
    kind: "citation",
    id: `citation-${i}-${cv.citation.raw_text}`,
    data: cv,
  }));

  const tierOrder: Record<FlagTier, number> = { critical: 0, review: 1, verified: 2 };
  return [...claimItems, ...citationItems].sort(
    (a, b) => tierOrder[tierOf(a)] - tierOrder[tierOf(b)]
  );
}

export const TIER_LABEL: Record<FlagTier, string> = {
  critical: "Critical",
  review: "Review",
  verified: "Verified",
};

export const STATUS_LABEL: Record<string, string> = {
  supported: "Supported",
  partially_supported: "Partially supported",
  overstated: "Overstated",
  contradicted: "Contradicted",
  unverifiable: "Unverifiable",
};
