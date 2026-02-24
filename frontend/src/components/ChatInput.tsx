"use client";

import {
  useState,
  useRef,
  useCallback,
  type KeyboardEvent,
  type ChangeEvent,
} from "react";
import Button from "./Button";

const ACCEPTED_FILES = ".mid,.midi,.wav,.mp3,.m4a,.ogg,.flac";

interface ChatInputProps {
  onSend: (text: string) => void;
  onFileUpload: (file: File) => void;
  isStreaming: boolean;
  onCancel: () => void;
}

export default function ChatInput({
  onSend,
  onFileUpload,
  isStreaming,
  onCancel,
}: ChatInputProps) {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const adjustHeight = useCallback(() => {
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = "auto";
      ta.style.height = `${Math.min(ta.scrollHeight, 200)}px`;
    }
  }, []);

  const handleSend = useCallback(() => {
    const trimmed = text.trim();
    if (!trimmed || isStreaming) return;
    onSend(trimmed);
    setText("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [text, isStreaming, onSend]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend],
  );

  const handleChange = useCallback(
    (e: ChangeEvent<HTMLTextAreaElement>) => {
      setText(e.target.value);
      adjustHeight();
    },
    [adjustHeight],
  );

  const handleFileChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        onFileUpload(file);
        e.target.value = "";
      }
    },
    [onFileUpload],
  );

  return (
    <div className="flex items-end gap-2" data-testid="chat-input">
      <input
        ref={fileInputRef}
        type="file"
        accept={ACCEPTED_FILES}
        className="hidden"
        onChange={handleFileChange}
        data-testid="file-input"
      />

      <Button
        variant="ghost"
        size="sm"
        onClick={() => fileInputRef.current?.click()}
        disabled={isStreaming}
        aria-label="Attach file"
        className="shrink-0"
      >
        <svg
          className="w-5 h-5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828L18 9.828a4 4 0 00-5.656-5.656L5.757 10.757a6 6 0 008.486 8.486L20.828 13"
          />
        </svg>
      </Button>

      <textarea
        ref={textareaRef}
        value={text}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder="Ask about chords, progressions, scales..."
        disabled={isStreaming}
        rows={1}
        className="flex-1 resize-none bg-bark-900 border border-bark-600 rounded-lg px-4 py-3
                   text-sm font-body text-amber-100 placeholder:text-bark-500
                   focus:outline-none focus:border-amber-400/50 focus:shadow-glow
                   transition-colors duration-fast disabled:opacity-50"
        data-testid="chat-textarea"
      />

      {isStreaming ? (
        <Button
          variant="danger"
          size="sm"
          onClick={onCancel}
          className="shrink-0"
        >
          Cancel
        </Button>
      ) : (
        <Button
          variant="primary"
          size="sm"
          onClick={handleSend}
          disabled={!text.trim()}
          className="shrink-0"
        >
          Send
        </Button>
      )}
    </div>
  );
}
