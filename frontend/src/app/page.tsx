"use client";

import { useState, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { ImageDropzone } from "@/components/image-dropzone";
import { CatfishGauge } from "@/components/catfish-gauge";
import { ScoreBreakdown } from "@/components/score-breakdown";
import { analyzeImage } from "@/lib/api";
import { CatfishResult } from "@/types/analysis";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [result, setResult] = useState<CatfishResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelected = useCallback((f: File) => {
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
    setError(null);
  }, []);

  const handleAnalyze = useCallback(async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await analyzeImage(file);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  }, [file]);

  return (
    <main className="min-h-screen bg-background">
      <div className="mx-auto max-w-2xl px-4 py-12">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold tracking-tight">
            Catfish Detector
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Upload a photo to check if it might be stolen or fake
          </p>
        </div>

        {/* Upload */}
        <ImageDropzone
          onFileSelected={handleFileSelected}
          onAnalyze={handleAnalyze}
          file={file}
          preview={preview}
          loading={loading}
        />

        {/* Error */}
        {error && (
          <Card className="mt-6 border-destructive/50 bg-destructive/5">
            <CardContent className="py-4 text-sm text-destructive">
              {error}
            </CardContent>
          </Card>
        )}

        {/* Loading skeleton */}
        {loading && (
          <div className="mt-8 space-y-6">
            <div className="flex flex-col items-center gap-4">
              <Skeleton className="h-[130px] w-[200px] rounded-full" />
              <Skeleton className="h-5 w-24" />
            </div>
            <Separator />
            <div className="space-y-3">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          </div>
        )}

        {/* Results */}
        {result && !loading && (
          <div className="mt-8 space-y-6 animate-in fade-in-0 slide-in-from-bottom-4 duration-500">
            <div className="flex justify-center">
              <CatfishGauge
                score={result.overall_score}
                verdict={result.verdict}
                durationMs={result.analysis_duration_ms}
              />
            </div>

            <Separator />

            <div>
              <h2 className="mb-3 text-sm font-medium text-muted-foreground uppercase tracking-wide">
                Analysis Breakdown
              </h2>
              <ScoreBreakdown result={result} />
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
