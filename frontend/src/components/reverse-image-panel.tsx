"use client";

import { ReverseImageResult } from "@/types/analysis";
import { Badge } from "@/components/ui/badge";

interface ReverseImagePanelProps {
  data: ReverseImageResult;
}

export function ReverseImagePanel({ data }: ReverseImagePanelProps) {
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-2 text-sm">
        <span className="text-muted-foreground">Total Matches</span>
        <span className="font-medium">{data.total_matches}</span>
        <span className="text-muted-foreground">Stock Sites</span>
        <span className="font-medium">
          {data.found_on_stock_sites ? (
            <span className="text-destructive">Yes</span>
          ) : (
            "No"
          )}
        </span>
        <span className="text-muted-foreground">Social Media</span>
        <span className="font-medium">
          {data.found_on_social_media ? "Yes" : "No"}
        </span>
      </div>

      {data.matches.length > 0 && (
        <div className="space-y-2 pt-2">
          <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide">
            Sources Found
          </p>
          <div className="space-y-1.5 max-h-48 overflow-y-auto">
            {data.matches.map((match, i) => (
              <div
                key={i}
                className="flex items-center gap-2 text-xs rounded-md bg-muted/50 px-3 py-2"
              >
                <a
                  href={match.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="truncate text-primary hover:underline flex-1"
                >
                  {match.page_title || new URL(match.source_url).hostname}
                </a>
                {match.is_stock_site && (
                  <Badge variant="destructive" className="text-[10px] shrink-0">
                    Stock
                  </Badge>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

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
