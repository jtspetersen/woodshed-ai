"use client";

import { useRef, useEffect, useCallback, useState } from "react";
import { useChat } from "@/hooks/useChat";
import { useStatus } from "@/hooks/useStatus";
import type { Creativity } from "@/components/CreativityControl";
import { uploadFile } from "@/lib/api";
import { getSessionId } from "@/lib/session";

import Logo from "./Logo";
import StatusBar from "./StatusBar";
import ExamplePrompts from "./ExamplePrompts";
import MessageBubble from "./MessageBubble";
import ChatInput from "./ChatInput";
import CreativityControl from "./CreativityControl";
import VUMeter from "./VUMeter";
import ThinkingIndicator from "./ThinkingIndicator";
import Button from "./Button";

export default function ChatInterface() {
  const {
    messages, isStreaming, error, statusStep, statusDetail,
    sendMessage, reset, cancel,
  } = useChat();
  const { status } = useStatus();
  const [creativity, setCreativity] = useState<Creativity>("Balanced");
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages or streaming updates
  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: isStreaming ? "instant" : "smooth",
    });
  }, [messages, isStreaming]);

  const handleSend = useCallback(
    (text: string) => {
      sendMessage(text, creativity);
    },
    [sendMessage, creativity],
  );

  const handleExampleSelect = useCallback(
    (prompt: string) => {
      sendMessage(prompt, creativity);
    },
    [sendMessage, creativity],
  );

  const handleFileUpload = useCallback(
    async (file: File) => {
      const result = await uploadFile(getSessionId(), file);
      if (result.error) {
        return;
      }
      if (result.analysis) {
        sendMessage(
          `I just uploaded "${file.name}". Here's the analysis: ${result.analysis}`,
          creativity,
        );
      }
    },
    [sendMessage, creativity],
  );

  return (
    <div
      className="flex flex-col h-screen max-h-screen"
      data-testid="chat-interface"
    >
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-3 border-b border-bark-800">
        <Logo size={32} />
        <StatusBar status={status} />
        <Button variant="ghost" size="sm" onClick={reset}>
          New Chat
        </Button>
      </header>

      {/* Messages area */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-4 py-6 space-y-4"
        data-testid="message-list"
      >
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-8">
            <div className="text-center">
              <h2 className="font-display text-2xl font-bold text-amber-400 mb-2">
                Welcome to Woodshed AI
              </h2>
              <p className="text-bark-400 font-body">
                Your AI-powered songwriting companion. Try one of these:
              </p>
            </div>
            <ExamplePrompts onSelect={handleExampleSelect} />
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            {isStreaming && (
              <div className="space-y-2">
                {statusStep ? (
                  <ThinkingIndicator
                    step={statusStep}
                    detail={statusDetail}
                    thinking={messages[messages.length - 1]?.thinking}
                  />
                ) : (
                  <div className="flex justify-start pl-4">
                    <VUMeter active />
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>

      {/* Error bar */}
      {error && (
        <div
          className="px-4 py-2 bg-rust-500/10 border-t border-rust-400 text-rust-300 text-sm font-body"
          data-testid="error-bar"
        >
          {error}
        </div>
      )}

      {/* Input area */}
      <footer className="px-4 py-3 border-t border-bark-800 space-y-2">
        <ChatInput
          onSend={handleSend}
          onFileUpload={handleFileUpload}
          isStreaming={isStreaming}
          onCancel={cancel}
        />
        <div className="flex justify-center">
          <CreativityControl
            value={creativity}
            onChange={setCreativity}
            disabled={isStreaming}
          />
        </div>
      </footer>
    </div>
  );
}
