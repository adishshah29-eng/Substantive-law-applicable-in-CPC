"use client";

import { useEffect, useState } from "react";

interface IntegrityRingProps {
  score: number;
  size?: number;
}

function colorForScore(score: number): string {
  // Destructive red (0) -> warning gold (50) -> success green (100),
  // interpolated in HSL space, desaturated to stay in the site's
  // restrained navy/gold palette rather than a loud traffic-light sweep.
  const hue = Math.max(0, Math.min(120, (score / 100) * 120));
  return `hsl(${hue}, 62%, 42%)`;
}

export function IntegrityRing({ score, size = 176 }: IntegrityRingProps) {
  const [animated, setAnimated] = useState(0);
  const stroke = 12;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;

  useEffect(() => {
    const raf = requestAnimationFrame(() => setAnimated(score));
    return () => cancelAnimationFrame(raf);
  }, [score]);

  const offset = circumference * (1 - animated / 100);
  const color = colorForScore(score);

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--border)"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 1s ease-out, stroke 1s ease-out" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-serif text-4xl font-medium text-foreground">
          {Math.round(score)}
        </span>
        <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Integrity
        </span>
      </div>
    </div>
  );
}
