"use client";

import { useRef, useEffect, useState } from "react";

interface SheetMusicProps {
  abc: string;
}

export default function SheetMusic({ abc }: SheetMusicProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const abcjs = await import("abcjs");
        if (cancelled || !containerRef.current) return;
        // forecolor/staffcolor/selectionColor are valid abcjs options
        // but missing from the @types/abcjs type definitions
        abcjs.renderAbc(containerRef.current, abc, {
          responsive: "resize",
          staffwidth: 600,
          scale: 0.8,
          ...({
            forecolor: "#FEECD2",        // amber-100
            selectionColor: "#F5A623",   // amber-400
            staffcolor: "#6B5B4B",       // bark-600
          } as Record<string, string>),
        });
      } catch {
        if (!cancelled) setError(true);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [abc]);

  if (error) {
    return (
      <pre
        className="font-mono text-sm bg-bark-800 border border-bark-600 rounded-md p-3 my-2 overflow-x-auto text-amber-100"
        data-testid="sheet-music-fallback"
      >
        {abc}
      </pre>
    );
  }

  return (
    <div
      ref={containerRef}
      className="bg-bark-800 border border-bark-600 rounded-md p-3 my-2 overflow-x-auto [&_svg]:max-w-full"
      data-testid="sheet-music"
    />
  );
}
