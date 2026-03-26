"use client";

import { MetadataResult } from "@/types/analysis";
import { Badge } from "@/components/ui/badge";

interface MetadataPanelProps {
  data: MetadataResult;
}

export function MetadataPanel({ data }: MetadataPanelProps) {
  const rows = [
    { label: "EXIF Data", value: data.has_exif ? "Present" : "Missing" },
    { label: "Camera", value: data.camera_make && data.camera_model ? `${data.camera_make} ${data.camera_model}` : null },
    { label: "Software", value: data.software },
    { label: "GPS Data", value: data.gps_present ? "Found" : "Not found" },
    { label: "Original Date", value: data.original_date },
    { label: "Thumbnail", value: data.has_thumbnail ? "Present" : "Missing" },
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
