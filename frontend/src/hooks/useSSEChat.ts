import { useState, useCallback, useRef } from "react";
import { ChatMessage, Citation } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function useSSEChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (queryText: string, topK: number = 4) => {
      const trimmed = queryText.trim();
      if (!trimmed || isStreaming) return;

      const userMsgId = `user-${Date.now()}`;
      const assistantMsgId = `assistant-${Date.now()}`;

      const userMsg: ChatMessage = {
        id: userMsgId,
        role: "user",
        content: trimmed,
        timestamp: Date.now(),
      };

      const assistantMsg: ChatMessage = {
        id: assistantMsgId,
        role: "assistant",
        content: "",
        citations: [],
        timestamp: Date.now(),
        isStreaming: true,
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setIsStreaming(true);

      abortControllerRef.current = new AbortController();

      try {
        const response = await fetch(`${API_BASE}/api/chat/stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            query: trimmed,
            top_k: topK,
            stream: true,
          }),
          signal: abortControllerRef.current.signal,
        });

        if (!response.ok || !response.body) {
          const errText = await response.text().catch(() => "");
          console.error("Backend response error:", response.status, errText);
          throw new Error(`HTTP error! status: ${response.status} - ${errText}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";
        let currentEventType = "message";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            const trimmedLine = line.trim();
            if (!trimmedLine) continue;

            if (trimmedLine.startsWith("event:")) {
              currentEventType = trimmedLine.replace("event:", "").trim();
              continue;
            }

            if (trimmedLine.startsWith("data:")) {
              const rawData = trimmedLine.replace("data:", "").trim();
              try {
                const parsed = JSON.parse(rawData);

                if (currentEventType === "metadata") {
                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === assistantMsgId
                        ? {
                            ...msg,
                            citations: parsed.citations || [],
                            cache_hit: parsed.cache_hit,
                          }
                        : msg
                    )
                  );
                } else if (currentEventType === "token") {
                  const tokenStr = parsed.token || "";
                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === assistantMsgId
                        ? {
                            ...msg,
                            content: msg.content + tokenStr,
                          }
                        : msg
                    )
                  );
                } else if (currentEventType === "done") {
                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === assistantMsgId
                        ? {
                            ...msg,
                            ttft_ms: parsed.ttft_ms,
                            total_time_ms: parsed.total_time_ms,
                            cache_hit: parsed.cache_hit,
                            isStreaming: false,
                          }
                        : msg
                    )
                  );
                }
              } catch (e) {
                console.warn("Failed to parse SSE payload:", rawData);
              }
            }
          }
        }
      } catch (err: any) {
        if (err.name !== "AbortError") {
          console.error("SSE Streaming Error:", err);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? {
                    ...msg,
                    content:
                      msg.content ||
                      "Error communicating with the SmartInsight backend. Please ensure the API is running.",
                    isStreaming: false,
                  }
                : msg
            )
          );
        }
      } finally {
        setIsStreaming(false);
        abortControllerRef.current = null;
      }
    },
    [isStreaming]
  );

  const stopStreaming = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsStreaming(false);
    }
  }, []);

  const clearChat = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    messages,
    isStreaming,
    sendMessage,
    stopStreaming,
    clearChat,
  };
}
