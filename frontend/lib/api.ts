import type { Report, ReportPollResult, SourceChunk } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function handle<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.text();
    throw new ApiError(body || response.statusText, response.status);
  }
  return response.json() as Promise<T>;
}

export async function verifyDocument(file: File): Promise<{ job_id: string; status: string }> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_URL}/verify`, { method: "POST", body: formData });
  return handle(response);
}

export async function getReport(jobId: string): Promise<ReportPollResult> {
  const response = await fetch(`${API_URL}/report/${jobId}`, { cache: "no-store" });
  return handle(response);
}

export async function getSource(sourceId: string): Promise<SourceChunk> {
  const response = await fetch(`${API_URL}/source/${sourceId}`, { cache: "no-store" });
  return handle(response);
}

export async function pollReport(
  jobId: string,
  { intervalMs = 2000, timeoutMs = 180000 }: { intervalMs?: number; timeoutMs?: number } = {}
): Promise<Report> {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const result = await getReport(jobId);
    if ("integrity_score" in result) return result as Report;
    if (result.status === "failed") {
      throw new Error(result.error || "Verification failed");
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
  throw new Error("Timed out waiting for report");
}
