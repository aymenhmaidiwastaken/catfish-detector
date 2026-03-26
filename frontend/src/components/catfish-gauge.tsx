"use client";

import { useEffect, useState } from "react";

interface CatfishGaugeProps {
  score: number;
  verdict: string;
  durationMs: number;
}

function getColor(score: number): string {
  if (score < 30) return "#22c55e";      // green
  if (score < 50) return "#eab308";      // yellow
  if (score < 65) return "#f97316";      // orange
  return "#ef4444";                       // red
}

export function CatfishGauge({ score, verdict, durationMs }: CatfishGaugeProps) {
  const [animatedScore, setAnimatedScore] = useState(0);

  useEffect(() => {
    let frame: number;
    const start = performance.now();
    const duration = 1200;

    const animate = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setAnimatedScore(Math.round(score * eased));

      if (progress < 1) {
        frame = requestAnimationFrame(animate);
      }
    };

    frame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frame);
  }, [score]);

  const size = 200;
  const strokeWidth = 12;
  const radius = (size - strokeWidth) / 2;
  const circumference = Math.PI * radius; // semicircle
  const offset = circumference - (animatedScore / 100) * circumference;
  const color = getColor(animatedScore);

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size / 2 + 30 }}>
        <svg
          width={size}
          height={size / 2 + strokeWidth}
          viewBox={`0 0 ${size} ${size / 2 + strokeWidth}`}
        >
          <defs>
            <linearGradient id="gauge-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#22c55e" />
              <stop offset="50%" stopColor="#eab308" />
              <stop offset="100%" stopColor="#ef4444" />
            </linearGradient>
          </defs>

          {/* Background arc */}
          <path
            d={`M ${strokeWidth / 2} ${size / 2} A ${radius} ${radius} 0 0 1 ${
              size - strokeWidth / 2
            } ${size / 2}`}
            fill="none"
            stroke="currentColor"
            className="text-muted/30"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />

          {/* Score arc */}
          <path
            d={`M ${strokeWidth / 2} ${size / 2} A ${radius} ${radius} 0 0 1 ${
              size - strokeWidth / 2
            } ${size / 2}`}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ transition: "stroke 0.3s ease" }}
          />
        </svg>

        {/* Score text */}
        <div
          className="absolute inset-0 flex flex-col items-center justify-end pb-2"
          style={{ height: size / 2 + strokeWidth }}
        >
          <span className="text-5xl font-bold tabular-nums" style={{ color }}>
            {animatedScore}
          </span>
        </div>
      </div>

      <span
        className="text-lg font-semibold"
        style={{ color }}
      >
        {verdict}
      </span>

      <span className="text-xs text-muted-foreground">
        Analyzed in {(durationMs / 1000).toFixed(1)}s
      </span>
    </div>
  );
}
