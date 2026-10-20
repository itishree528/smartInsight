import React, { useState, useRef } from "react";
import { Document, UploadStep } from "@/types";
import { uploadPDF, deleteDocument } from "@/lib/api";
import { formatBytes } from "@/lib/utils";
import {
  UploadCloud,
  FileCheck2,
  Trash2,
  Layers,
  AlertCircle,
  CheckCircle2,
  FileText,
} from "lucide-react";

interface DocumentUploadProps {
  documents: Document[];
  onDocumentsChange: () => void;
}

export function DocumentUpload({
  documents,
  onDocumentsChange,
}: DocumentUploadProps) {
  const [step, setStep] = useState<UploadStep>("idle");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setErrorMsg("Please upload a PDF document (.pdf only).");
      return;
    }

    setErrorMsg(null);
    const result = await uploadPDF(file, (s) => setStep(s));

    if (!result.success) {
      setErrorMsg(result.message);
    } else {
      onDocumentsChange();
      setTimeout(() => setStep("idle"), 2500);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleDelete = async (id: string) => {
    const ok = await deleteDocument(id);
    if (ok) {
      onDocumentsChange();
    }
  };

  const getStepProgress = (currentStep: UploadStep) => {
    switch (currentStep) {
      case "uploading":
        return { pct: 25, label: "1/4: Uploading PDF to server..." };
      case "parsing":
        return { pct: 50, label: "2/4: Extracting text & pages via pypdf..." };
      case "chunking":
        return { pct: 75, label: "3/4: Creating semantic overlapping chunks..." };
      case "indexing":
        return { pct: 95, label: "4/4: Computing dense vectors & storing in pgvector..." };
      case "completed":
        return { pct: 100, label: "Indexing Complete!" };
      default:
        return { pct: 0, label: "" };
    }
  };

  const progress = getStepProgress(step);

  return (
    <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 flex flex-col h-full backdrop-blur-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <UploadCloud className="w-5 h-5 text-indigo-400" />
          <h2 className="text-base font-semibold text-white">
            Document Ingestion &amp; pgvector Pipeline
          </h2>
        </div>
        <span className="text-xs font-mono text-slate-400">
          {documents.length} Indexed {documents.length === 1 ? "Doc" : "Docs"}
        </span>
      </div>

      {/* Drag & Drop Upload Zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-all ${
          isDragging
            ? "border-brand-500 bg-brand-500/10"
            : "border-slate-800 hover:border-slate-700 bg-slate-950/40"
        }`}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={(e) => {
            if (e.target.files && e.target.files.length > 0) {
              handleFileUpload(e.target.files[0]);
            }
          }}
          accept=".pdf"
          className="hidden"
        />

        <div className="flex flex-col items-center justify-center gap-2">
          <div className="w-10 h-10 rounded-full bg-slate-900 flex items-center justify-center text-slate-400">
            <UploadCloud className="w-5 h-5 text-brand-400" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-200">
              Click to select PDF or drag and drop
            </p>
            <p className="text-[11px] text-slate-500 mt-0.5">
              Automated chunking &amp; 1536-dim vector indexing
            </p>
          </div>
        </div>
      </div>

      {/* Upload Progress Status Indicator */}
      {step !== "idle" && (
        <div className="mt-4 p-3 rounded-xl bg-slate-950 border border-slate-800">
          <div className="flex items-center justify-between text-xs mb-1.5">
            <span className="text-slate-300 font-medium">{progress.label}</span>
            <span className="font-mono text-brand-400">{progress.pct}%</span>
          </div>
          <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${
                step === "completed" ? "bg-emerald-500" : "bg-brand-500"
              }`}
              style={{ width: `${progress.pct}%` }}
            />
          </div>
        </div>
      )}

      {/* Error alert */}
      {errorMsg && (
        <div className="mt-3 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Document Repository List */}
      <div className="mt-5 flex-1 flex flex-col min-h-0">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2.5">
          Indexed Documents
        </h3>

        {documents.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-6 text-slate-500 text-xs border border-dashed border-slate-800/80 rounded-xl">
            <FileText className="w-8 h-8 text-slate-600 mb-2" />
            <p>No documents uploaded yet.</p>
            <p className="text-[11px] text-slate-600 mt-1">
              Upload any PDF above to begin querying with pgvector.
            </p>
          </div>
        ) : (
          <div className="space-y-2 overflow-y-auto max-h-[220px] pr-1">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800/60 hover:border-slate-700 transition-colors"
              >
                <div className="flex items-center gap-2.5 truncate">
                  <div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center shrink-0">
                    <FileCheck2 className="w-4 h-4 text-brand-400" />
                  </div>
                  <div className="truncate">
                    <p
                      className="text-xs font-medium text-slate-200 truncate"
                      title={doc.filename}
                    >
                      {doc.filename}
                    </p>
                    <div className="flex items-center gap-2 text-[10px] text-slate-400 mt-0.5">
                      <span>{formatBytes(doc.file_size)}</span>
                      <span>•</span>
                      <span>{doc.total_pages} {doc.total_pages === 1 ? "page" : "pages"}</span>
                      <span>•</span>
                      <span className="flex items-center gap-0.5 text-indigo-400">
                        <Layers className="w-3 h-3" />
                        {doc.chunk_count} chunks
                      </span>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => handleDelete(doc.id)}
                  className="p-1.5 text-slate-500 hover:text-rose-400 rounded-lg hover:bg-slate-800 transition-colors shrink-0"
                  title="Delete Document"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
