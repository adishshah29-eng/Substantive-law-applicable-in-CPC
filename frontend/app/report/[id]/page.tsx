"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { AlertTriangle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CategoryRollup } from "@/components/CategoryRollup";
import { ClaimCard } from "@/components/ClaimCard";
import { EvidencePanel } from "@/components/EvidencePanel";
import { ExportReportButton } from "@/components/ExportReportButton";
import { IntegrityRing } from "@/components/IntegrityRing";
import { pollReport } from "@/lib/api";
import { buildFlagItems, tierOf, type FlagItem, type FlagTier } from "@/lib/flags";
import type { Report } from "@/lib/types";

type TabValue = "all" | FlagTier;

export default function ReportPage() {
  const params = useParams<{ id: string }>();
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<TabValue>("all");
  const [selected, setSelected] = useState<FlagItem | null>(null);

  useEffect(() => {
    let cancelled = false;
    pollReport(params.id)
      .then((r) => {
        if (!cancelled) setReport(r);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load report");
      });
    return () => {
      cancelled = true;
    };
  }, [params.id]);

  const flagItems = useMemo(
    () => (report ? buildFlagItems(report.claims, report.citation_verdicts) : []),
    [report]
  );

  const counts = useMemo(() => {
    const base = { all: flagItems.length, critical: 0, review: 0, verified: 0 };
    for (const item of flagItems) base[tierOf(item)]++;
    return base;
  }, [flagItems]);

  const visibleItems = tab === "all" ? flagItems : flagItems.filter((i) => tierOf(i) === tab);

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background px-6 text-foreground">
        <div className="max-w-md text-center">
          <p className="text-lg font-medium text-destructive">Something went wrong</p>
          <p className="mt-2 text-sm text-muted-foreground">{error}</p>
        </div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="min-h-screen bg-background px-6 py-12 text-foreground">
        <div className="mx-auto max-w-4xl space-y-6">
          <Skeleton className="h-10 w-64 bg-muted" />
          <div className="flex gap-6">
            <Skeleton className="h-44 w-44 rounded-full bg-muted" />
            <Skeleton className="h-44 flex-1 bg-muted" />
          </div>
          <Skeleton className="h-64 w-full bg-muted" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background px-6 py-12 text-foreground">
      <div id="veritas-report" className="mx-auto max-w-4xl">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="font-serif text-xl font-medium text-foreground">{report.filename}</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              {new Date(report.generated_at).toLocaleString()} · {report.total_claims_analyzed}{" "}
              claims analyzed · {report.processing_time_seconds.toFixed(1)}s
            </p>
          </div>
          <ExportReportButton targetId="veritas-report" filename={report.job_id} />
        </div>

        <div className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-[176px_1fr]">
          <div className="flex items-center justify-center">
            <IntegrityRing score={report.integrity_score} />
          </div>
          <CategoryRollup breakdown={report.category_breakdown} />
        </div>

        {report.procedural_risk_flag && (
          <Alert className="mt-6 border-destructive/30 bg-destructive-muted text-destructive">
            <AlertTriangle className="h-4 w-4 text-destructive" />
            <AlertTitle className="text-destructive">Procedural risk</AlertTitle>
            <AlertDescription className="text-destructive/90">
              {report.procedural_risk_summary}
            </AlertDescription>
          </Alert>
        )}

        <div className="mt-8">
          <Tabs value={tab} onValueChange={(v) => setTab(v as TabValue)}>
            <TabsList className="border border-border bg-card">
              <TabsTrigger value="all">All ({counts.all})</TabsTrigger>
              <TabsTrigger value="critical">Critical ({counts.critical})</TabsTrigger>
              <TabsTrigger value="review">Review ({counts.review})</TabsTrigger>
              <TabsTrigger value="verified">Verified ({counts.verified})</TabsTrigger>
            </TabsList>
          </Tabs>

          <div className="mt-4 space-y-2.5">
            {visibleItems.length === 0 && (
              <p className="py-8 text-center text-sm text-muted-foreground">
                Nothing in this category.
              </p>
            )}
            {visibleItems.map((item) => (
              <ClaimCard key={item.id} item={item} onClick={() => setSelected(item)} />
            ))}
          </div>
        </div>
      </div>

      <Sheet open={selected !== null} onOpenChange={(open) => !open && setSelected(null)}>
        <SheetContent className="w-full overflow-y-auto border-border bg-card text-foreground sm:max-w-2xl">
          <SheetHeader>
            <SheetTitle className="font-serif text-foreground">Claim detail</SheetTitle>
          </SheetHeader>
          <div className="mt-6">{selected && <EvidencePanel item={selected} />}</div>
        </SheetContent>
      </Sheet>
    </div>
  );
}
