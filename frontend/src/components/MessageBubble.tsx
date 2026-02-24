"use client";

import { useMemo, useState, useEffect, lazy, Suspense } from "react";
import dynamic from "next/dynamic";
import type { DisplayMessage } from "@/lib/types";
import { renderMarkdown } from "@/lib/markdown";
import { getFileUrl, getMidiDataUri } from "@/lib/api";
import { extractMusicBlocks } from "@/lib/music-detection";
import GuitarTab from "./GuitarTab";
import ToolCallBlock from "./ToolCallBlock";

const SheetMusic = lazy(() => import("./SheetMusic"));
const MidiPlayer = dynamic(() => import("./MidiPlayer"), { ssr: false });

interface MessageBubbleProps {
  message: DisplayMessage;
}

/** Splits content into alternating text + music block segments for inline rendering. */
function useContentSegments(content: string, isAssistant: boolean) {
  return useMemo(() => {
    if (!isAssistant) return [{ type: "text" as const, content }];

    const blocks = extractMusicBlocks(content);
    if (blocks.length === 0) return [{ type: "text" as const, content }];

    const segments: Array<
      | { type: "text"; content: string }
      | { type: "abc"; content: string }
      | { type: "tab"; content: string }
    > = [];

    let cursor = 0;
    for (const block of blocks) {
      if (block.start > cursor) {
        segments.push({ type: "text", content: content.slice(cursor, block.start) });
      }
      segments.push({ type: block.type as "abc" | "tab", content: block.content });
      cursor = block.end;
    }
    if (cursor < content.length) {
      segments.push({ type: "text", content: content.slice(cursor) });
    }

    return segments;
  }, [content, isAssistant]);
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const segments = useContentSegments(message.content, !isUser);

  // Check if any attached files are MIDI for inline playback
  const midiFiles = message.files?.filter(
    (f) => f.endsWith(".mid") || f.endsWith(".midi"),
  );

  return (
    <div
      className={`flex ${isUser ? "justify-end" : "justify-start"}`}
      data-testid="message-bubble"
      data-role={message.role}
    >
      <div
        className={`max-w-[80%] px-4 py-3 ${
          isUser
            ? "bg-bark-700 rounded-lg rounded-br-none"
            : "bg-bark-900 border border-bark-700 rounded-lg rounded-bl-none"
        }`}
      >
        {/* Thinking block (assistant only, collapsible) */}
        {!isUser && message.thinking && (
          <ThinkingBlock thinking={message.thinking} />
        )}

        {/* Tool call blocks (assistant only) */}
        {!isUser && message.toolCalls && message.toolCalls.length > 0 && (
          <ToolCallBlock toolCalls={message.toolCalls} />
        )}

        {segments.map((seg, i) => {
          if (seg.type === "text") {
            return (
              <div
                key={i}
                className="font-body text-sm text-amber-100
                           [&_strong]:font-bold [&_em]:italic
                           [&_pre]:my-2 [&_code]:text-amber-300
                           [&_a]:text-amber-400 [&_a]:underline"
                dangerouslySetInnerHTML={{ __html: renderMarkdown(seg.content) }}
              />
            );
          }
          if (seg.type === "abc") {
            return (
              <Suspense
                key={i}
                fallback={
                  <pre className="font-mono text-sm bg-bark-800 p-3 my-2 rounded-md text-amber-100">
                    {seg.content}
                  </pre>
                }
              >
                <SheetMusic abc={seg.content} />
              </Suspense>
            );
          }
          if (seg.type === "tab") {
            return <GuitarTab key={i} tab={seg.content} />;
          }
          return null;
        })}

        {/* Inline MIDI players for attached MIDI files */}
        {midiFiles && midiFiles.length > 0 && (
          <div className="mt-2" data-testid="midi-players">
            {midiFiles.map((file) => {
              const filename = file.includes("/")
                ? file.split("/").pop()!
                : file.includes("\\")
                  ? file.split("\\").pop()!
                  : file;
              return (
                <Suspense
                  key={file}
                  fallback={
                    <div className="text-bark-400 text-sm my-2">
                      Loading MIDI player...
                    </div>
                  }
                >
                  <MidiPlayerWithDataUri filename={filename} />
                </Suspense>
              );
            })}
          </div>
        )}

        {/* File download links */}
        {message.files && message.files.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-bark-600">
            {message.files.map((file) => {
              const filename = file.includes("/")
                ? file.split("/").pop()!
                : file.includes("\\")
                  ? file.split("\\").pop()!
                  : file;
              return (
                <a
                  key={file}
                  href={getFileUrl(filename)}
                  download
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full
                             bg-bark-800 border border-bark-600 text-xs font-mono
                             text-amber-400 hover:border-amber-400 transition-colors duration-fast"
                  data-testid="file-link"
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
                  {filename}
                </a>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

/** Fetches MIDI data URI and renders player */
function MidiPlayerWithDataUri({ filename }: { filename: string }) {
  // Use a simple state approach for data URI fetching
  const { useMidiSrc } = useMidiDataUriHook(filename);
  return <MidiPlayer src={useMidiSrc} />;
}

/** Minimal hook to fetch MIDI data URI */
function useMidiDataUriHook(filename: string) {
  const [src, setSrc] = useState("");

  useEffect(() => {
    let cancelled = false;
    getMidiDataUri(filename)
      .then((res) => {
        if (!cancelled) setSrc(res.data_uri);
      })
      .catch(() => {
        // Fall back to direct download URL
        if (!cancelled) setSrc(getFileUrl(filename));
      });
    return () => {
      cancelled = true;
    };
  }, [filename]);

  return { useMidiSrc: src };
}

/** Collapsible block showing LLM reasoning */
function ThinkingBlock({ thinking }: { thinking: string }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="my-1 text-xs" data-testid="thinking-block">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1.5 text-bark-500 hover:text-bark-400
                   transition-colors duration-fast"
        data-testid="thinking-block-toggle"
      >
        <svg
          className={`w-3 h-3 shrink-0 transition-transform duration-fast ${
            open ? "rotate-90" : ""
          }`}
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
        <span className="font-mono">Reasoning</span>
      </button>
      {open && (
        <pre
          className="mt-1 font-mono text-bark-500 whitespace-pre-wrap break-words
                     max-h-48 overflow-y-auto bg-bark-900/50 rounded-md px-3 py-2
                     border border-bark-700"
        >
          {thinking}
        </pre>
      )}
    </div>
  );
}
