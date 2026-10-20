"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Header } from "@/components/Header";
import { AnalyticsPanel } from "@/components/AnalyticsPanel";
import { DocumentUpload } from "@/components/DocumentUpload";
import { ChatInterface } from "@/components/ChatInterface";
import { useSSEChat } from "@/hooks/useSSEChat";
import { fetchDocuments, fetchAnalyticsStats } from "@/lib/api";
import { Document, AnalyticsStats } from "@/types";

export default function Home() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [stats, setStats] = useState<AnalyticsStats | null>(null);
  const [isLoadingStats, setIsLoadingStats] = useState(false);

  const { messages, isStreaming, sendMessage, stopStreaming, clearChat } =
    useSSEChat();

  const loadData = useCallback(async () => {
    setIsLoadingStats(true);
    const [docs, currentStats] = await Promise.all([
      fetchDocuments(),
      fetchAnalyticsStats(),
    ]);
    setDocuments(docs);
    setStats(currentStats);
    setIsLoadingStats(false);
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Re-fetch stats after a message finished streaming to reflect real-time metrics
  useEffect(() => {
    if (!isStreaming && messages.length > 0) {
      fetchAnalyticsStats().then((s) => s && setStats(s));
    }
  }, [isStreaming, messages.length]);

  return (
    <div className="flex flex-col min-h-screen bg-slate-950 text-slate-100">
      <Header />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 space-y-6 flex flex-col">
        {/* Top Telemetry & Performance Row */}
        <AnalyticsPanel
          stats={stats}
          onRefresh={loadData}
          isLoading={isLoadingStats}
        />

        {/* Two-Column Responsive Workspace */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 min-h-[580px]">
          {/* Left Column: PDF Ingestion & pgvector Pipeline (4 cols) */}
          <div className="lg:col-span-5 h-[580px] lg:h-auto">
            <DocumentUpload
              documents={documents}
              onDocumentsChange={loadData}
            />
          </div>

          {/* Right Column: Real-time SSE Chat & Source Citations (7 cols) */}
          <div className="lg:col-span-7 h-[580px] lg:h-auto">
            <ChatInterface
              messages={messages}
              isStreaming={isStreaming}
              onSendMessage={sendMessage}
              onStopStreaming={stopStreaming}
              onClearChat={clearChat}
            />
          </div>
        </div>
      </main>

      <footer className="border-t border-slate-900 py-3 text-center text-xs text-slate-400">
        <p>
          SmartInsight • FastAPI, Next.js, pgvector (HNSW cosine index), Redis Caching Layer
        </p>
      </footer>
    </div>
  );
}
