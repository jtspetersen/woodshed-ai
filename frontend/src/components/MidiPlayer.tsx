"use client";

import { useEffect, useRef, useState } from "react";

interface MidiPlayerProps {
  /** URL or data URI pointing to a MIDI file */
  src: string;
}

export default function MidiPlayer({ src }: MidiPlayerProps) {
  const [loaded, setLoaded] = useState(false);
  const vizRef = useRef<HTMLElement>(null);
  const playerRef = useRef<HTMLElement>(null);

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

  // Configure visualizer with taller notes + link player ↔ visualizer
  useEffect(() => {
    if (!loaded || !vizRef.current) return;

    const viz = vizRef.current as HTMLElement & {
      config?: Record<string, unknown>;
      reload?: () => void;
      noteSequence?: { notes?: Array<{ pitch: number }> };
    };

    // Set taller noteHeight so labels fit inside the bars
    viz.config = {
      noteHeight: 16,
      noteSpacing: 2,
      pixelsPerTimeStep: 60,
      noteRGB: "245, 166, 35",      // amber-400
      activeNoteRGB: "224, 109, 69", // rust-400
    };

    // Link player ↔ visualizer so the cursor tracks during playback
    if (playerRef.current) {
      const player = playerRef.current as HTMLElement & { addVisualizer?: (v: unknown) => void };
      if (typeof player.addVisualizer === "function") {
        player.addVisualizer(viz);
      }
    }
  }, [loaded, src]);

  // Add note name labels (C4, E5, etc.) onto the piano roll note bars.
  // Magenta re-renders SVG content during playback (active note highlighting),
  // so we observe the container and re-inject labels when they disappear.
  useEffect(() => {
    if (!loaded || !vizRef.current || !src) return;

    const NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
    const midiName = (p: number) => `${NAMES[p % 12]}${Math.floor(p / 12) - 1}`;
    const viz = vizRef.current;

    function injectLabels() {
      // Find the current SVG (Magenta may replace it)
      const svg = viz.querySelector("svg");
      if (!svg) return false;

      // Remove stale labels before re-injecting
      svg.querySelector(".note-labels")?.remove();

      const noteRects = svg.querySelectorAll("rect.note");
      if (noteRects.length === 0) return false;

      const svgNs = "http://www.w3.org/2000/svg";
      const group = document.createElementNS(svgNs, "g");
      group.setAttribute("class", "note-labels");

      for (const rect of noteRects) {
        const y = parseFloat(rect.getAttribute("y") || "0");
        const h = parseFloat(rect.getAttribute("height") || "0");
        const x = parseFloat(rect.getAttribute("x") || "0");
        const w = parseFloat(rect.getAttribute("width") || "0");

        // Read pitch from data attribute (set by Magenta visualizer)
        const pitchAttr = rect.getAttribute("data-pitch")
          ?? (rect as SVGRectElement & { dataset: DOMStringMap }).dataset?.pitch;
        if (!pitchAttr) continue;
        const pitch = parseInt(pitchAttr, 10);
        if (isNaN(pitch)) continue;
        const label = midiName(pitch);

        if (w < 24) continue;

        const text = document.createElementNS(svgNs, "text");
        text.setAttribute("x", String(x + 3));
        text.setAttribute("y", String(y + h * 0.75));
        text.setAttribute("font-size", String(Math.min(h * 0.65, 11)));
        text.setAttribute("font-family", "JetBrains Mono, monospace");
        text.setAttribute("fill", "#1A1310");
        text.setAttribute("pointer-events", "none");
        text.textContent = label;
        group.appendChild(text);
      }

      if (group.childNodes.length > 0) {
        svg.appendChild(group);
        return true;
      }
      return false;
    }

    // Poll until the SVG renders note rects
    let attempts = 0;
    const timer = setInterval(() => {
      if (++attempts > 30) { clearInterval(timer); return; }
      if (injectLabels()) clearInterval(timer);
    }, 300);

    // Observe the visualizer container (not the SVG) so we catch Magenta
    // replacing or re-rendering the SVG during playback. Debounce to avoid
    // rapid-fire re-injection during active note highlighting.
    let debounceTimer: ReturnType<typeof setTimeout>;
    const observer = new MutationObserver(() => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        const svg = viz.querySelector("svg");
        if (svg && svg.querySelector("rect.note") && !svg.querySelector(".note-labels")) {
          injectLabels();
        }
      }, 100);
    });
    observer.observe(viz, { childList: true, subtree: true });

    return () => {
      clearInterval(timer);
      clearTimeout(debounceTimer);
      observer.disconnect();
    };
  }, [loaded, src]);

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
      className="bg-bark-800 border border-bark-600 rounded-md p-4 my-2 space-y-3"
      data-testid="midi-player"
    >
      {/* Header */}
      <div className="flex items-center gap-2">
        <svg
          className="w-4 h-4 text-amber-400"
          fill="currentColor"
          viewBox="0 0 20 20"
          aria-hidden="true"
        >
          <path d="M18 3a1 1 0 00-1.196-.98l-10 2A1 1 0 006 5v9.114A4.369 4.369 0 005 14c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V7.82l8-1.6v5.894A4.37 4.37 0 0015 12c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V3z" />
        </svg>
        <span className="text-sm font-display font-semibold text-amber-200">
          MIDI Playback
        </span>
      </div>

      {loaded ? (
        <>
          {/* Visualizer */}
          <div className="overflow-hidden rounded-sm">
            {/* @ts-expect-error html-midi-player web component */}
            <midi-visualizer
              ref={vizRef}
              src={src}
              type="piano-roll"
              data-testid="midi-visualizer"
            />
          </div>

          {/* Player controls */}
          <div className="border-t border-bark-700 pt-3">
            {/* @ts-expect-error html-midi-player web component */}
            <midi-player
              ref={playerRef}
              src={src}
              sound-font="https://storage.googleapis.com/magentadata/js/soundfonts/sgm_plus"
              data-testid="midi-player-element"
            />
          </div>
        </>
      ) : (
        <div className="text-bark-400 text-sm" data-testid="midi-player-loading">
          Loading MIDI player...
        </div>
      )}

      {/* Download */}
      <a
        href={src}
        download
        className="inline-flex items-center gap-1.5 rounded-full transition-all duration-normal ease-out
                   bg-transparent text-amber-400 border border-bark-600 hover:border-amber-400
                   font-display font-semibold text-sm px-3 py-1"
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
