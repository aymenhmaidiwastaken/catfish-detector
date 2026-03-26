"use client";

import { FaceAnalysisResult } from "@/types/analysis";
import { Badge } from "@/components/ui/badge";

interface FaceAnalysisPanelProps {
  data: FaceAnalysisResult;
}

export function FaceAnalysisPanel({ data }: FaceAnalysisPanelProps) {
  const rows = [
    { label: "Faces Detected", value: String(data.faces_detected) },
    { label: "Dominant Emotion", value: data.dominant_emotion },
    { label: "Estimated Age", value: data.estimated_age ? `~${data.estimated_age}` : null },
    { label: "Gender", value: data.gender },
    {
      label: "Face Confidence",
      value: data.face_confidence ? `${(data.face_confidence * 100).toFixed(1)}%` : null,
    },
    { label: "High Quality", value: data.is_high_quality ? "Yes" : "No" },
  ];

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-2 text-sm">
        {rows.map(({ label, value }) => (
          <div key={label} className="contents">
            <span className="text-muted-foreground">{label}</span>
            <span className="font-medium">{value || "N/A"}</span>
          </div>
        ))}
      </div>

      {data.suspicious_signals.length > 0 && (
        <div className="flex flex-wrap gap-1.5 pt-2">
          {data.suspicious_signals.map((signal, i) => (
            <Badge key={i} variant="secondary" className="text-xs">
              {signal}
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}
