import type { StatusResponse } from "@/lib/types";

interface StatusBarProps {
  status: StatusResponse | null;
}

interface StatusDotProps {
  ok: boolean;
  label: string;
}

function StatusDot({ ok, label }: StatusDotProps) {
  return (
    <span className="flex items-center gap-1.5 text-xs font-mono text-bark-400">
      <span
        className={`w-2 h-2 rounded-full ${ok ? "bg-sage-400" : "bg-rust-400"}`}
        data-testid={`status-dot-${label.toLowerCase().replace(/\s/g, "-")}`}
      />
      {label}
    </span>
  );
}

export default function StatusBar({ status }: StatusBarProps) {
  return (
    <div
      className="flex items-center gap-4 px-4 py-2 bg-bark-900 rounded-md border border-bark-600"
      data-testid="status-bar"
    >
      <StatusDot
        ok={status?.ollama.available ?? false}
        label="Ollama"
      />
      <StatusDot
        ok={(status?.knowledge_base.documents ?? 0) > 0}
        label="Knowledge Base"
      />
      <StatusDot
        ok={status?.transcription.available ?? false}
        label="Transcription"
      />
      {status?.ollama.available && (
        <span className="text-xs font-mono text-bark-500 ml-auto">
          {status.ollama.models[0]}
        </span>
      )}
    </div>
  );
}
