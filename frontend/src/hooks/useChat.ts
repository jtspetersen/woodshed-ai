"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import type { ContentPart, DisplayMessage } from "@/lib/types";
import type { Creativity } from "@/components/CreativityControl";
import { streamChat, resetChat } from "@/lib/api";
import { getSessionId, resetSessionId } from "@/lib/session";

export function useChat() {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusStep, setStatusStep] = useState<string | null>(null);
  const [statusDetail, setStatusDetail] = useState<string | null>(null);

  const sessionIdRef = useRef(getSessionId());
  const controllerRef = useRef<AbortController | null>(null);
  const tokenBufferRef = useRef("");
  const rafIdRef = useRef<number | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      controllerRef.current?.abort();
      if (rafIdRef.current !== null) {
        cancelAnimationFrame(rafIdRef.current);
      }
    };
  }, []);

  const flushTokens = useCallback(() => {
    rafIdRef.current = null;
    const buffered = tokenBufferRef.current;
    if (!buffered) return;
    tokenBufferRef.current = "";
    setMessages((prev) => {
      const next = [...prev];
      const last = next[next.length - 1];
      // Update content (backward compat) and parts[] simultaneously
      const parts = [...(last.parts ?? [])];
      const lastPart = parts[parts.length - 1];
      if (lastPart && lastPart.type === "text") {
        parts[parts.length - 1] = { type: "text", text: lastPart.text + buffered };
      } else {
        parts.push({ type: "text", text: buffered });
      }
      next[next.length - 1] = { ...last, content: last.content + buffered, parts };
      return next;
    });
  }, []);

  const sendMessage = useCallback(
    (text: string, creativity: Creativity) => {
      setError(null);
      setStatusStep(null);
      setStatusDetail(null);

      const userMsg: DisplayMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: text,
      };
      const assistantMsg: DisplayMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: "",
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setIsStreaming(true);
      tokenBufferRef.current = "";

      const controller = streamChat(
        sessionIdRef.current,
        text,
        creativity,
        {
          onToken: (token) => {
            setStatusStep(null);
            setStatusDetail(null);
            tokenBufferRef.current += token;
            if (rafIdRef.current === null) {
              rafIdRef.current = requestAnimationFrame(flushTokens);
            }
          },
          onStatus: (step, detail) => {
            setStatusStep(step);
            if (detail) setStatusDetail(detail);
          },
          onThinking: (text) => {
            setMessages((prev) => {
              const next = [...prev];
              const last = next[next.length - 1];
              const existing = last.thinking ?? "";
              next[next.length - 1] = {
                ...last,
                thinking: existing + text,
              };
              return next;
            });
          },
          onToolCall: (toolCall) => {
            setMessages((prev) => {
              const next = [...prev];
              const last = next[next.length - 1];
              const existing = last.toolCalls ?? [];
              next[next.length - 1] = {
                ...last,
                toolCalls: [...existing, toolCall],
              };
              return next;
            });
          },
          onFiles: (files) => {
            flushTokens();
            setMessages((prev) => {
              const next = [...prev];
              const last = next[next.length - 1];
              next[next.length - 1] = { ...last, files };
              return next;
            });
          },
          onPart: (part: ContentPart) => {
            // Non-text parts break the current text stream —
            // flush tokens first so text part is finalized
            if (part.type !== "text") {
              flushTokens();
            }
            setMessages((prev) => {
              const next = [...prev];
              const last = next[next.length - 1];
              const parts = [...(last.parts ?? [])];
              if (part.type === "text") {
                // Append to last text part or create new
                const lastPart = parts[parts.length - 1];
                if (lastPart && lastPart.type === "text") {
                  parts[parts.length - 1] = { type: "text", text: lastPart.text + part.text };
                } else {
                  parts.push(part);
                }
              } else {
                parts.push(part);
              }
              next[next.length - 1] = { ...last, parts };
              return next;
            });
          },
          onDone: () => {
            flushTokens();
            setIsStreaming(false);
            setStatusStep(null);
            setStatusDetail(null);
            controllerRef.current = null;
          },
          onError: (message) => {
            flushTokens();
            setError(message);
            setIsStreaming(false);
            setStatusStep(null);
            setStatusDetail(null);
            controllerRef.current = null;
          },
        },
      );

      controllerRef.current = controller;
    },
    [flushTokens],
  );

  const cancel = useCallback(() => {
    controllerRef.current?.abort();
    controllerRef.current = null;
    if (rafIdRef.current !== null) {
      cancelAnimationFrame(rafIdRef.current);
      rafIdRef.current = null;
    }
    // Flush remaining tokens
    const buffered = tokenBufferRef.current;
    if (buffered) {
      tokenBufferRef.current = "";
      setMessages((prev) => {
        const next = [...prev];
        const last = next[next.length - 1];
        const parts = [...(last.parts ?? [])];
        const lastPart = parts[parts.length - 1];
        if (lastPart && lastPart.type === "text") {
          parts[parts.length - 1] = { type: "text", text: lastPart.text + buffered };
        } else {
          parts.push({ type: "text", text: buffered });
        }
        next[next.length - 1] = { ...last, content: last.content + buffered, parts };
        return next;
      });
    }
    setIsStreaming(false);
    setStatusStep(null);
    setStatusDetail(null);
  }, []);

  const reset = useCallback(async () => {
    cancel();
    await resetChat(sessionIdRef.current);
    sessionIdRef.current = resetSessionId();
    setMessages([]);
    setError(null);
    setStatusStep(null);
    setStatusDetail(null);
  }, [cancel]);

  return { messages, isStreaming, error, statusStep, statusDetail, sendMessage, reset, cancel };
}
