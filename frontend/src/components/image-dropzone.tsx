"use client";

import { useCallback, useState, useRef } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface ImageDropzoneProps {
  onFileSelected: (file: File) => void;
  onAnalyze: () => void;
  file: File | null;
  preview: string | null;
  loading: boolean;
}

export function ImageDropzone({
  onFileSelected,
  onAnalyze,
  file,
  preview,
  loading,
}: ImageDropzoneProps) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    (f: File) => {
      if (f.type.startsWith("image/")) {
        onFileSelected(f);
      }
    },
    [onFileSelected]
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const f = e.dataTransfer.files[0];
      if (f) handleFile(f);
    },
    [handleFile]
  );

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  }, []);

  const onDragLeave = useCallback(() => setDragging(false), []);

  const onChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const f = e.target.files?.[0];
      if (f) handleFile(f);
    },
    [handleFile]
  );

  return (
    <Card
      className={`relative flex flex-col items-center justify-center gap-4 border-2 border-dashed p-8 transition-colors cursor-pointer ${
        dragging
          ? "border-primary bg-primary/5"
          : preview
          ? "border-muted"
          : "border-muted-foreground/25 hover:border-muted-foreground/50"
      }`}
      onDrop={onDrop}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onClick={() => !preview && inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        className="hidden"
        onChange={onChange}
      />

      {preview ? (
        <div className="flex flex-col items-center gap-4 w-full">
          <div className="relative w-48 h-48 rounded-lg overflow-hidden">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={preview}
              alt="Upload preview"
              className="w-full h-full object-cover"
            />
          </div>
          <p className="text-sm text-muted-foreground">{file?.name}</p>
          <div className="flex gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                inputRef.current?.click();
              }}
            >
              Change
            </Button>
            <Button
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onAnalyze();
              }}
              disabled={loading}
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                  Analyzing...
                </span>
              ) : (
                "Analyze Image"
              )}
            </Button>
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-2 py-8">
          <svg
            className="h-10 w-10 text-muted-foreground/50"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
            />
          </svg>
          <p className="text-sm text-muted-foreground">
            Drop an image here or click to upload
          </p>
          <p className="text-xs text-muted-foreground/60">
            JPEG, PNG, WebP up to 10MB
          </p>
        </div>
      )}
    </Card>
  );
}
