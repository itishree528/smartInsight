import React, { useState, useRef, useEffect } from "react";
import { ChatMessage } from "@/types";
import { CitationCard } from "@/components/CitationCard";
import {
  Send,
  Square,
  Sparkles,
  Zap,
  Clock,
  Trash2,
  Database,
  ArrowRight,
} from "lucide-react";

interface ChatInterfaceProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  onSendMessage: (query: string, topK: number) => void;
  onStopStreaming: () => void;
  onClearChat: () => void;
}

const SAMPLE_PROMPTS = [
  "Summarize the key architecture and components in this document",
  "What performance benchmarks and latency numbers are reported?",
  "How does the pgvector cosine similarity search function?",
  "What are the benefits of the Redis caching layer?",
];

export function ChatInterface({
  messages,
  isStreaming,
  onSendMessage,
  onStopStreaming,
  onClearChat,
}: ChatInterfaceProps) {
  const [input, setInput] = useState("");
  const [topK, setTopK] = useState(4);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;
    onSendMessage(input, topK);
    setInput("");
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl flex flex-col h-full backdrop-blur-sm overflow-hidden">
      {/* Chat Header */}
      <div className="px-5 py-4 border-b border-slate-800/80 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-brand-400" />
          <h2 className="text-base font-semibold text-white">
            Real-Time Semantic Chat Preview
          </h2>
        </div>

        <div className="flex items-center gap-3">
          {/* Top-K Selector */}
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <span>Top-K:</span>
            <select
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="bg-slate-950 border border-slate-800 rounded-lg px-2 py-1 text-slate-200 text-xs focus:outline-none focus:border-brand-500"
            >
              <option value={2}>2 chunks</option>
              <option value={4}>4 chunks</option>
              <option value={6}>6 chunks</option>
            </select>
          </div>

          {messages.length > 0 && (
            <button
              onClick={onClearChat}
              className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors text-xs flex items-center gap-1"
              title="Clear chat history"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Messages Stream Area */}
      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-400">
            <div className="w-12 h-12 rounded-2xl bg-brand-500/10 flex items-center justify-center text-brand-400 mb-3 border border-brand-500/20">
              <Sparkles className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-semibold text-slate-200">
              Ask anything about your uploaded documents
            </h3>
            <p className="text-xs text-slate-400 max-w-md mt-1 mb-6">
              Queries execute cosine similarity vector retrieval on pgvector and
              stream responses with Server-Sent Events (SSE) in &lt;350ms TTFT.
            </p>

            {/* Suggested Prompts */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 w-full max-w-xl text-left">
              {SAMPLE_PROMPTS.map((prompt, idx) => (
                <button
                  key={idx}
                  onClick={() => onSendMessage(prompt, topK)}
                  className="p-2.5 rounded-xl bg-slate-950/70 border border-slate-800/80 hover:border-brand-500/40 hover:bg-slate-800/50 transition-all text-xs text-slate-300 flex items-center justify-between group"
                >
                  <span className="truncate pr-2">{prompt}</span>
                  <ArrowRight className="w-3 h-3 text-slate-500 group-hover:text-brand-400 shrink-0" />
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col ${
                msg.role === "user" ? "items-end" : "items-start"
              }`}
            >
              {/* Message Bubble */}
              <div
                className={`max-w-[85%] rounded-2xl p-4 text-xs leading-relaxed ${
                  msg.role === "user"
                    ? "bg-brand-600 text-white rounded-br-xs shadow-md"
                    : "bg-slate-950/80 border border-slate-800/90 text-slate-200 rounded-bl-xs"
                }`}
              >
                {/* Assistant Telemetry Badges */}
                {msg.role === "assistant" && (
                  <div className="flex flex-wrap items-center gap-2 mb-3 pb-2.5 border-b border-slate-800/80 text-[11px]">
                    {/* TTFT Indicator */}
                    {msg.ttft_ms !== undefined && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/20 font-mono">
                        <Clock className="w-3 h-3" />
                        <span>TTFT: {msg.ttft_ms}ms</span>
                        <span className="text-[9px] text-amber-500/70">(&lt;350ms)</span>
                      </span>
                    )}

                    {/* Redis Cache Status Indicator */}
                    {msg.cache_hit !== undefined && (
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border font-mono ${
                          msg.cache_hit
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                            : "bg-indigo-500/10 text-indigo-400 border-indigo-500/20"
                        }`}
                      >
                        {msg.cache_hit ? (
                          <>
                            <Zap className="w-3 h-3 text-emerald-400" />
                            <span>Redis: HIT (Instant)</span>
                          </>
                        ) : (
                          <>
                            <Database className="w-3 h-3 text-indigo-400" />
                            <span>pgvector Cosine: MISS</span>
                          </>
                        )}
                      </span>
                    )}
                  </div>
                )}

                {/* Message Content */}
                <div className="whitespace-pre-wrap font-sans text-slate-200 text-xs leading-relaxed">
                  {msg.content}
                  {msg.isStreaming && (
                    <span className="inline-block w-1.5 h-3.5 bg-brand-400 ml-1 animate-blink" />
                  )}
                </div>

                {/* Source Citation Cards */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-slate-800/80">
                    <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-400 mb-2">
                      <Database className="w-3.5 h-3.5 text-brand-400" />
                      <span>
                        Source Citations ({msg.citations.length} pgvector chunks)
                      </span>
                    </div>

                    <div className="grid grid-cols-1 gap-2">
                      {msg.citations.map((c, i) => (
                        <CitationCard key={i} citation={c} index={i} />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <form
        onSubmit={handleSubmit}
        className="p-4 border-t border-slate-800/80 bg-slate-950/40"
      >
        <div className="relative flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about your indexed documents..."
            disabled={isStreaming}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-4 pr-24 py-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
          />

          <div className="absolute right-2 flex items-center gap-1.5">
            {isStreaming ? (
              <button
                type="button"
                onClick={onStopStreaming}
                className="p-2 rounded-lg bg-rose-500 hover:bg-rose-600 text-white transition-colors"
                title="Stop streaming"
              >
                <Square className="w-3.5 h-3.5 fill-current" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!input.trim()}
                className="p-2 rounded-lg bg-brand-600 hover:bg-brand-500 disabled:bg-slate-800 text-white transition-colors disabled:opacity-40"
                title="Send query"
              >
                <Send className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      </form>
    </div>
  );
}
