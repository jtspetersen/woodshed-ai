"use client";

import { useState } from "react";
import type { ToolCallInfo } from "@/lib/types";

/** Human-readable labels for tool names. */
const TOOL_LABELS: Record<string, string> = {
  analyze_chord: "Broke down that chord",
  analyze_progression: "Analyzed the progression",
  suggest_next_chord: "Found what comes next",
  get_scale_for_mood: "Matched scales to the vibe",
  detect_key: "Figured out the key",
  get_chord_voicings: "Looked up voicings",
  get_related_chords: "Explored related chords",
  generate_progression_midi: "Built your MIDI file",
  generate_scale_midi: "Wrote out the scale",
  generate_guitar_tab: "Drew up the tab",
  generate_notation: "Wrote notation",
  export_for_daw: "Packaged for your DAW",
  analyze_midi: "Studied the MIDI file",
  transcribe_audio: "Transcribed the audio",
};

function formatArgs(args: Record<string, unknown> | null): string {
  if (!args) return "";
  return Object.entries(args)
    .map(([k, v]) => {
      if (Array.isArray(v)) return `${k}: [${v.join(", ")}]`;
      if (typeof v === "string") return `${k}: "${v}"`;
      return `${k}: ${v}`;
    })
    .join(", ");
}

function formatResult(result: Record<string, unknown> | string | null): string {
  if (result === null) return "No result";
  if (typeof result === "string") return result;
  return JSON.stringify(result, null, 2);
}

interface ToolCallBlockProps {
  toolCalls: ToolCallInfo[];
}

export default function ToolCallBlock({ toolCalls }: ToolCallBlockProps) {
  const [expanded, setExpanded] = useState<number | null>(null);

  return (
    <div
      className="space-y-1 my-2 text-sm"
      data-testid="tool-call-block"
    >
      {toolCalls.map((tc, i) => {
        const label = TOOL_LABELS[tc.name] ?? tc.name;
        const isOpen = expanded === i;

        return (
          <div key={i} className="border border-bark-700 rounded-md overflow-hidden">
            <button
              type="button"
              onClick={() => setExpanded(isOpen ? null : i)}
              className="flex items-center gap-2 w-full px-3 py-1.5 text-left
                         text-bark-300 hover:bg-bark-800/50 transition-colors duration-fast"
              data-testid="tool-call-toggle"
            >
              <svg
                className={`w-3 h-3 shrink-0 transition-transform duration-fast ${isOpen ? "rotate-90" : ""}`}
                fill="currentColor"
                viewBox="0 0 20 20"
                aria-hidden="true"
              >
                <path
                  fillRule="evenodd"
                  d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z"
                  clipRule="evenodd"
                />
              </svg>
              <span className="text-amber-400 font-mono text-xs">{label}</span>
              <span className="text-bark-500 font-mono text-xs truncate">
                ({formatArgs(tc.arguments)})
              </span>
            </button>

            {isOpen && (
              <div className="px-3 py-2 bg-bark-900 border-t border-bark-700">
                <pre className="text-xs font-mono text-bark-300 whitespace-pre-wrap break-words max-h-48 overflow-y-auto">
                  {formatResult(tc.result)}
                </pre>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
