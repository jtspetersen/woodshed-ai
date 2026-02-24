"use client";

import { useEffect, useState } from "react";

interface MidiPlayerProps {
  /** URL or data URI pointing to a MIDI file */
  src: string;
}

export default function MidiPlayer({ src }: MidiPlayerProps) {
  const [loaded, setLoaded] = useState(false);

  // Load html-midi-player via CDN script tag to avoid webpack bundling
  // the @magenta/music → tone dependency chain (broken ESM exports).
  useEffect(() => {
    if (customElements.get("midi-player")) {
      setLoaded(true);
      return;
    }
    const script = document.createElement("script");
    script.src =
      "https://cdn.jsdelivr.net/combine/npm/tone@14.7.77,npm/@magenta/music@1.23.1/es6/core.js,npm/html-midi-player@1.6.0";
    script.async = true;
    script.onload = () => setLoaded(true);
    script.onerror = () => {}; // Fallback renders
    document.head.appendChild(script);
  }, []);

  if (!src) {
    return (
      <div
        className="text-bark-400 text-sm italic my-2"
        data-testid="midi-player-empty"
      >
        No MIDI source available.
      </div>
    );
  }

  return (
    <div
      className="bg-bark-800 border border-bark-600 rounded-md p-3 my-2 space-y-2"
      data-testid="midi-player"
    >
      {loaded ? (
        <>
          {/* @ts-expect-error html-midi-player web component */}
          <midi-visualizer
            src={src}
            type="piano-roll"
            data-testid="midi-visualizer"
          />
          {/* @ts-expect-error html-midi-player web component */}
          <midi-player
            src={src}
            sound-font="https://storage.googleapis.com/magentadata/js/soundfonts/sgm_plus"
            data-testid="midi-player-element"
          />
        </>
      ) : (
        <div className="text-bark-400 text-sm" data-testid="midi-player-loading">
          Loading MIDI player...
        </div>
      )}
      <a
        href={src}
        download
        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full
                   bg-bark-900 border border-bark-600 text-xs font-mono
                   text-amber-400 hover:border-amber-400 transition-colors duration-fast"
        data-testid="midi-download"
      >
        <svg
          className="w-3.5 h-3.5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M12 4v12m0 0l-4-4m4 4l4-4M4 18h16"
          />
        </svg>
        Download MIDI
      </a>
    </div>
  );
}
