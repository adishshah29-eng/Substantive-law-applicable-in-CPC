import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import type { FlagItem } from "@/lib/flags";
import { STATUS_LABEL, sourceLabel, tierOf } from "@/lib/flags";
import { cn } from "@/lib/utils";

const TIER_BADGE_CLASSES: Record<string, string> = {
  critical: "bg-destructive-muted text-destructive border-destructive/30",
  review: "bg-warning-muted text-warning border-warning/30",
  verified: "bg-success-muted text-success border-success/30",
};

interface ClaimCardProps {
  item: FlagItem;
  onClick: () => void;
}

export function ClaimCard({ item, onClick }: ClaimCardProps) {
  const tier = tierOf(item);

  const text =
    item.kind === "claim" ? item.data.claim.sentence.text : item.data.citation.raw_text;
  const badgeLabel =
    item.kind === "claim"
      ? STATUS_LABEL[item.data.verdict.status]
      : item.data.verified
        ? "Verified"
        : "Fabricated citation";
  const topSource = item.kind === "claim" ? item.data.retrieved_sources[0]?.chunk : undefined;
  const citationLine =
    item.kind === "claim"
      ? topSource
        ? sourceLabel(topSource)
        : null
      : item.data.citation.raw_text;

  return (
    <Card
      onClick={onClick}
      className="cursor-pointer border-border bg-card p-4 transition-colors hover:border-primary/30 hover:bg-muted/30"
    >
      <div className="flex items-start justify-between gap-4">
        <p className="line-clamp-2 flex-1 text-sm text-foreground">{text}</p>
        <Badge
          variant="outline"
          className={cn("shrink-0 whitespace-nowrap", TIER_BADGE_CLASSES[tier])}
        >
          {badgeLabel}
        </Badge>
      </div>
      {citationLine && (
        <p className="mt-2 truncate font-mono text-xs text-muted-foreground">{citationLine}</p>
      )}
    </Card>
  );
}
