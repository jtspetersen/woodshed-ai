"use client";

import { useState } from "react";

interface ThinkingIndicatorProps {
  step: string;
  detail?: string | null;
  thinking?: string | null;
}

export default function ThinkingIndicator({
  step,
  detail,
  thinking,
}: ThinkingIndicatorProps) {
  const [expanded, setExpanded] = useState(false);
  const hasExtra = !!(detail || thinking);

  return (
    <div className="pl-4" data-testid="thinking-indicator">
      <button
        type="button"
        onClick={() => hasExtra && setExpanded((e) => !e)}
        className={`flex items-center gap-2 text-sm text-bark-400 font-body ${
          hasExtra ? "cursor-pointer hover:text-bark-300" : "cursor-default"
        }`}
        data-testid="thinking-toggle"
      >
        <span className="inline-flex gap-0.5">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
          <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse [animation-delay:150ms]" />
          <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse [animation-delay:300ms]" />
        </span>
        <span>{step}</span>
        {hasExtra && (
          <svg
            className={`w-3 h-3 transition-transform duration-fast ${
              expanded ? "rotate-90" : ""
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
        )}
      </button>

      {expanded && hasExtra && (
        <div
          className="mt-1 ml-6 space-y-2 text-xs"
          data-testid="thinking-detail"
        >
          {detail && (
            <div className="text-bark-500 font-mono">{detail}</div>
          )}
          {thinking && (
            <pre
              className="font-mono text-bark-500 whitespace-pre-wrap break-words
                         max-h-40 overflow-y-auto bg-bark-900 rounded-md px-3 py-2
                         border border-bark-700"
              data-testid="thinking-content"
            >
              {thinking}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
