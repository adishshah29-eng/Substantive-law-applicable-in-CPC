"use client";

import { useCallback, useState } from "react";
import { useDropzone, type FileRejection } from "react-dropzone";
import { FileText, UploadCloud } from "lucide-react";
import { cn } from "@/lib/utils";

interface UploadDropzoneProps {
  onFileAccepted: (file: File) => void;
  disabled?: boolean;
}

export function UploadDropzone({ onFileAccepted, disabled }: UploadDropzoneProps) {
  const [rejected, setRejected] = useState<string | null>(null);

  const onDrop = useCallback(
    (acceptedFiles: File[], fileRejections: FileRejection[]) => {
      if (fileRejections.length > 0) {
        setRejected(fileRejections[0].errors[0]?.message || "File not accepted");
        return;
      }
      setRejected(null);
      if (acceptedFiles[0]) onFileAccepted(acceptedFiles[0]);
    },
    [onFileAccepted]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    disabled,
    maxFiles: 1,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    },
  });

  return (
    <div>
      <div
        {...getRootProps()}
        className={cn(
          "flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed px-8 py-16 text-center transition-colors",
          isDragActive
            ? "border-primary bg-primary/5"
            : "border-border bg-card hover:border-primary/40 hover:bg-muted/40",
          disabled && "pointer-events-none opacity-50"
        )}
      >
        <input {...getInputProps()} />
        {isDragActive ? (
          <UploadCloud className="mb-4 h-10 w-10 text-primary" />
        ) : (
          <FileText className="mb-4 h-10 w-10 text-muted-foreground" />
        )}
        <p className="text-base font-medium text-foreground">
          {isDragActive ? "Drop the document here" : "Drag and drop a legal document"}
        </p>
        <p className="mt-1 text-sm text-muted-foreground">or click to browse — PDF or DOCX</p>
      </div>
      {rejected && <p className="mt-3 text-sm text-destructive">{rejected}</p>}
    </div>
  );
}
