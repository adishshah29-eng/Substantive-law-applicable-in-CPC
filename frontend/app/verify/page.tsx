"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, Loader2 } from "lucide-react";
import { UploadDropzone } from "@/components/UploadDropzone";
import { getReport, verifyDocument } from "@/lib/api";
import { cn } from "@/lib/utils";

const STEPS = ["Parsing", "Classifying", "Verifying", "Aggregating"] as const;
const STEP_INTERVAL_MS = 3500;

export default function VerifyPage() {
  const router = useRouter();
  const [fileName, setFileName] = useState<string | null>(null);
  const [stepIndex, setStepIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const pollTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const stepTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (pollTimer.current) clearInterval(pollTimer.current);
      if (stepTimer.current) clearInterval(stepTimer.current);
    };
  }, []);

  async function handleFile(file: File) {
    setError(null);
    setFileName(file.name);
    setRunning(true);
    setStepIndex(0);

    stepTimer.current = setInterval(() => {
      setStepIndex((i) => Math.min(i + 1, STEPS.length - 2));
    }, STEP_INTERVAL_MS);

    try {
      const { job_id } = await verifyDocument(file);

      pollTimer.current = setInterval(async () => {
        try {
          const result = await getReport(job_id);
          if ("integrity_score" in result) {
            if (stepTimer.current) clearInterval(stepTimer.current);
            if (pollTimer.current) clearInterval(pollTimer.current);
            setStepIndex(STEPS.length - 1);
            setTimeout(() => router.push(`/report/${job_id}`), 400);
          } else if (result.status === "failed") {
            if (stepTimer.current) clearInterval(stepTimer.current);
            if (pollTimer.current) clearInterval(pollTimer.current);
            setError(result.error || "Verification failed");
            setRunning(false);
          }
        } catch {
          // transient poll failure; keep trying until the next interval
        }
      }, 2000);
    } catch (err) {
      if (stepTimer.current) clearInterval(stepTimer.current);
      setError(err instanceof Error ? err.message : "Upload failed");
      setRunning(false);
    }
  }

  return (
    <div className="min-h-screen bg-background px-6 py-16 text-foreground">
      <div className="mx-auto max-w-xl">
        <h1 className="font-serif text-2xl font-medium text-foreground">Verify a document</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Upload an AI-assisted legal draft. VERITAS checks every substantive and
          procedural claim against Indian statute and case law.
        </p>

        <div className="mt-8">
          {!running ? (
            <UploadDropzone onFileAccepted={handleFile} />
          ) : (
            <div className="rounded-lg border border-border bg-card p-8">
              <p className="mb-6 truncate text-sm text-muted-foreground">{fileName}</p>
              <ol className="space-y-4">
                {STEPS.map((step, i) => (
                  <li key={step} className="flex items-center gap-3">
                    {i < stepIndex ? (
                      <CheckCircle2 className="h-5 w-5 shrink-0 text-success" />
                    ) : i === stepIndex ? (
                      <Loader2 className="h-5 w-5 shrink-0 animate-spin text-primary" />
                    ) : (
                      <div className="h-5 w-5 shrink-0 rounded-full border border-border" />
                    )}
                    <span
                      className={cn(
                        "text-sm",
                        i <= stepIndex ? "text-foreground" : "text-muted-foreground"
                      )}
                    >
                      {step}
                    </span>
                  </li>
                ))}
              </ol>
            </div>
          )}
        </div>

        {error && (
          <div className="mt-6 rounded-lg border border-destructive/30 bg-destructive-muted px-4 py-3 text-sm text-destructive">
            {error}
          </div>
        )}
      </div>
    </div>
  );
}
