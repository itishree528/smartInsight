import React, { useState } from "react";
import { Citation } from "@/types";
import { FileText, ChevronDown, ChevronUp, CheckCircle2 } from "lucide-react";
import { formatSimilarity } from "@/lib/utils";

interface CitationCardProps {
  citation: Citation;
  index: number;
}

export function CitationCard({ citation, index }: CitationCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const simScore = citation.similarity_score;
  const simPercent = formatSimilarity(simScore);

  const getBadgeColor = (score: number) => {
    if (score >= 0.8) return "bg-emerald-500/15 text-emerald-400 border-emerald-500/30";
    if (score >= 0.6) return "bg-blue-500/15 text-blue-400 border-blue-500/30";
    return "bg-slate-500/15 text-slate-400 border-slate-500/30";
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5 hover:border-slate-700 transition-all text-xs">
      {/* Top Header */}
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-2 truncate">
          <div className="w-6 h-6 rounded-lg bg-indigo-500/10 flex items-center justify-center shrink-0">
            <FileText className="w-3.5 h-3.5 text-indigo-400" />
          </div>
          <span
            className="font-medium text-slate-200 truncate max-w-[180px]"
            title={citation.document_name}
          >
            {citation.document_name}
          </span>
          <span className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] text-slate-300 font-mono">
            p. {citation.page_number}
          </span>
        </div>

        {/* Cosine Similarity Badge */}
        <div
          className={`flex items-center gap-1 px-2 py-0.5 rounded-full border text-[11px] font-semibold shrink-0 ${getBadgeColor(
            simScore
          )}`}
          title={`Cosine similarity score: ${simScore.toFixed(4)}`}
        >
          <CheckCircle2 className="w-3 h-3" />
          <span>{simPercent} match</span>
        </div>
      </div>

      {/* Snippet Content */}
      <div className="text-slate-300 font-mono text-[11px] leading-relaxed bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/60">
        <p className={isExpanded ? "" : "line-clamp-2"}>
          {citation.text_content}
        </p>
      </div>

      {/* Expand/Collapse Toggle */}
      {citation.text_content.length > 140 && (
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="mt-2 flex items-center gap-1 text-[11px] text-indigo-400 hover:text-indigo-300 font-medium transition-colors"
        >
          {isExpanded ? (
            <>
              <ChevronUp className="w-3 h-3" />
              <span>Show less</span>
            </>
          ) : (
            <>
              <ChevronDown className="w-3 h-3" />
              <span>Show full chunk</span>
            </>
          )}
        </button>
      )}
    </div>
  );
}
