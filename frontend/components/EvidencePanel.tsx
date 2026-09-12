"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { getSource } from "@/lib/api";
import type { FlagItem } from "@/lib/flags";
import { STATUS_LABEL } from "@/lib/flags";
import type { SourceChunk } from "@/lib/types";

function SourceLabel({ chunk }: { chunk: SourceChunk }) {
  if (chunk.source_type === "judgment") {
    return (
      <span>
        {chunk.case_name}
        {chunk.citation_string ? `, ${chunk.citation_string}` : ""}
        {chunk.court ? ` (${chunk.court.replace("_", " ")})` : ""}
      </span>
    );
  }
  const parts = [chunk.act_name];
  if (chunk.section_number) parts.push(`Section ${chunk.section_number}`);
  if (chunk.order_number) parts.push(`Order ${chunk.order_number}`);
  if (chunk.rule_number) parts.push(`Rule ${chunk.rule_number}`);
  return <span>{parts.filter(Boolean).join(", ")}</span>;
}

function FullSourceButton({ sourceId }: { sourceId: string }) {
  const [open, setOpen] = useState(false);
  const [chunk, setChunk] = useState<SourceChunk | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleOpen() {
    setOpen(true);
    if (chunk) return;
    setLoading(true);
    setError(null);
    try {
      setChunk(await getSource(sourceId));
    } catch {
      setError("Could not load the full source.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Button variant="outline" size="sm" onClick={handleOpen} className="mt-2">
        View full source
      </Button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-h-[80vh] max-w-2xl overflow-y-auto border-border bg-card text-foreground">
          <DialogHeader>
            <DialogTitle className="font-mono text-sm">
              {chunk ? <SourceLabel chunk={chunk} /> : sourceId}
            </DialogTitle>
          </DialogHeader>
          {loading && <p className="text-sm text-muted-foreground">Loading…</p>}
          {error && <p className="text-sm text-destructive">{error}</p>}
          {chunk && (
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground">
              {chunk.text}
            </p>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}

export function EvidencePanel({ item }: { item: FlagItem }) {
  if (item.kind === "citation") {
    const cv = item.data;
    return (
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Claimed citation
          </h3>
          <p className="mt-2 font-mono text-sm text-foreground">{cv.citation.raw_text}</p>
          {cv.citation.case_name && (
            <p className="mt-1 text-sm text-muted-foreground">{cv.citation.case_name}</p>
          )}
        </div>
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Verification result
          </h3>
          <Badge
            variant="outline"
            className={
              cv.verified
                ? "mt-2 border-success/30 bg-success-muted text-success"
                : "mt-2 border-destructive/30 bg-destructive-muted text-destructive"
            }
          >
            {cv.verified ? "Verified" : "Not verified"}
          </Badge>
          <p className="mt-2 text-sm leading-relaxed text-foreground">{cv.reason}</p>
          {cv.matched_case_name && (
            <p className="mt-2 text-sm text-muted-foreground">
              Matched: <span className="text-foreground">{cv.matched_case_name}</span>
            </p>
          )}
        </div>
      </div>
    );
  }

  const { claim, verdict } = item.data;
  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Claim
        </h3>
        <p className="mt-2 text-sm leading-relaxed text-foreground">{claim.sentence.text}</p>

        <div className="mt-4">
          <Badge variant="outline" className="border-border text-foreground">
            {STATUS_LABEL[verdict.status]}
          </Badge>
        </div>

        <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{verdict.reasoning}</p>

        {verdict.missing_elements.length > 0 && (
          <div className="mt-4">
            <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Missing elements
            </h4>
            <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-warning">
              {verdict.missing_elements.map((el) => (
                <li key={el}>{el}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Evidence
        </h3>
        <div className="mt-2 space-y-4">
          {verdict.evidence.length === 0 && (
            <p className="text-sm text-muted-foreground">No evidence span was cited.</p>
          )}
          {verdict.evidence.map((ev, i) => (
            <div key={i} className="rounded-lg border border-border bg-muted/40 p-3">
              <p className="font-mono text-xs text-muted-foreground">{ev.source_citation}</p>
              <p className="mt-2 text-sm leading-relaxed text-foreground">
                &ldquo;{ev.quoted_text}&rdquo;
              </p>
              <FullSourceButton sourceId={ev.source_id} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
