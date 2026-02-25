"use client";

import { useState, useEffect, lazy, Suspense } from "react";
import dynamic from "next/dynamic";
import type { ContentPart, DisplayMessage } from "@/lib/types";
import { renderMarkdown } from "@/lib/markdown";
import { getFileUrl, getMidiDataUri } from "@/lib/api";
import GuitarTab from "./GuitarTab";
import ToolCallBlock from "./ToolCallBlock";

const SheetMusic = lazy(() => import("./SheetMusic"));
const MidiPlayer = dynamic(() => import("./MidiPlayer"), { ssr: false });

interface MessageBubbleProps {
  message: DisplayMessage;
}

/** Renders a single content part with the appropriate component. */
function PartRenderer({ part }: { part: ContentPart }) {
  switch (part.type) {
    case "text":
      if (!part.text.trim()) return null;
      return (
        <div
          className="font-body text-sm text-amber-100
                     [&_strong]:font-bold [&_em]:italic
                     [&_pre]:my-2 [&_code]:text-amber-300
                     [&_a]:text-amber-400 [&_a]:underline"
          dangerouslySetInnerHTML={{ __html: renderMarkdown(part.text) }}
        />
      );
    case "abc":
      return (
        <Suspense
          fallback={
            <pre className="font-mono text-sm bg-bark-800 p-3 my-2 rounded-md text-amber-100">
              {part.abc}
            </pre>
          }
        >
          <SheetMusic abc={part.abc} />
        </Suspense>
      );
    case "tab":
      return <GuitarTab tab={part.tab} />;
    case "midi":
      return (
        <Suspense
          fallback={
            <div className="text-bark-400 text-sm my-2">
              Loading MIDI player...
            </div>
          }
        >
          <MidiPlayerWithDataUri filename={part.filename} />
        </Suspense>
      );
    case "file":
      return <FileDownloadLink filename={part.filename} />;
  }
}

/** Download link pill for a non-MIDI file. */
function FileDownloadLink({ filename }: { filename: string }) {
  return (
    <a
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
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  // Build parts array — use message.parts if available, else construct from content + files
  let parts: ContentPart[];
  if (message.parts && message.parts.length > 0) {
    parts = message.parts;
  } else {
    parts = [{ type: "text" as const, text: message.content }];
    // Legacy: if files are present but no parts, generate midi/file parts from files
    if (message.files) {
      for (const f of message.files) {
        const filename = f.includes("/")
          ? f.split("/").pop()!
          : f.includes("\\")
            ? f.split("\\").pop()!
            : f;
        if (f.endsWith(".mid") || f.endsWith(".midi")) {
          parts.push({ type: "midi", filename });
        } else {
          parts.push({ type: "file", filename });
        }
      }
    }
  }

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

        {/* Declarative content parts rendering */}
        {parts.map((part, i) => (
          <PartRenderer key={i} part={part} />
        ))}
      </div>
    </div>
  );
}

/** Fetches MIDI data URI and renders player */
function MidiPlayerWithDataUri({ filename }: { filename: string }) {
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
