"use client";

import { useState } from "react";
import { Download, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ExportReportButtonProps {
  targetId: string;
  filename: string;
}

export function ExportReportButton({ targetId, filename }: ExportReportButtonProps) {
  const [exporting, setExporting] = useState(false);

  async function handleExport() {
    const element = document.getElementById(targetId);
    if (!element) return;
    setExporting(true);
    try {
      const html2pdf = (await import("html2pdf.js")).default;
      await html2pdf()
        .set({
          filename: `${filename}-veritas-report.pdf`,
          margin: 10,
          html2canvas: { scale: 2, backgroundColor: "#f8fafc" },
          jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
        })
        .from(element)
        .save();
    } finally {
      setExporting(false);
    }
  }

  return (
    <Button variant="outline" onClick={handleExport} disabled={exporting} className="gap-2">
      {exporting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
      Export PDF
    </Button>
  );
}
