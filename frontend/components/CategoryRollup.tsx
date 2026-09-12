import { AlertTriangle, BadgeCheck, FileWarning, Gavel, ShieldAlert, XCircle } from "lucide-react";
import type { CategoryBreakdown } from "@/lib/types";
import { Card } from "@/components/ui/card";

interface Row {
  label: string;
  value: number;
  icon: React.ComponentType<{ className?: string }>;
  tone: "good" | "warn" | "bad";
}

const TONE_CLASSES: Record<Row["tone"], string> = {
  good: "text-success",
  warn: "text-warning",
  bad: "text-destructive",
};

export function CategoryRollup({ breakdown }: { breakdown: CategoryBreakdown }) {
  const rows: Row[] = [
    { label: "Substantive law verified", value: breakdown.substantive_verified, icon: BadgeCheck, tone: "good" },
    { label: "CPC procedure verified", value: breakdown.cpc_verified, icon: Gavel, tone: "good" },
    { label: "Citations verified", value: breakdown.citations_verified, icon: BadgeCheck, tone: "good" },
    { label: "Unsupported / overstated", value: breakdown.unsupported_propositions, icon: FileWarning, tone: "warn" },
    { label: "Procedural issues", value: breakdown.procedural_issues, icon: ShieldAlert, tone: "warn" },
    { label: "Conflicting authorities", value: breakdown.conflicting_authorities, icon: AlertTriangle, tone: "bad" },
    { label: "Fabricated citations", value: breakdown.fabricated_citations, icon: XCircle, tone: "bad" },
  ];

  return (
    <Card className="border-border bg-card p-5">
      <h2 className="mb-4 text-sm font-semibold text-foreground">Category breakdown</h2>
      <ul className="space-y-3">
        {rows.map((row) => (
          <li key={row.label} className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <row.icon className={`h-4 w-4 ${TONE_CLASSES[row.tone]}`} />
              <span className="text-sm text-foreground">{row.label}</span>
            </div>
            <span
              className={`text-sm font-semibold tabular-nums ${row.value > 0 ? TONE_CLASSES[row.tone] : "text-muted-foreground"}`}
            >
              {row.value}
            </span>
          </li>
        ))}
      </ul>
    </Card>
  );
}
