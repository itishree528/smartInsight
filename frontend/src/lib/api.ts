import { Document, AnalyticsStats, UploadStep } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchDocuments(): Promise<Document[]> {
  try {
    const res = await fetch(`${API_BASE}/api/documents`);
    if (!res.ok) throw new Error("Failed to load documents");
    return await res.json();
  } catch (err) {
    console.error("fetchDocuments error:", err);
    return [];
  }
}

export async function uploadPDF(
  file: File,
  onStepChange?: (step: UploadStep) => void
): Promise<{ success: boolean; message: string; document?: Document }> {
  try {
    onStepChange?.("uploading");
    const formData = new FormData();
    formData.append("file", file);

    // Simulate progress feedback transitions
    const parseTimer = setTimeout(() => onStepChange?.("parsing"), 400);
    const chunkTimer = setTimeout(() => onStepChange?.("chunking"), 900);
    const indexTimer = setTimeout(() => onStepChange?.("indexing"), 1400);

    const res = await fetch(`${API_BASE}/api/documents/upload`, {
      method: "POST",
      body: formData,
    });

    clearTimeout(parseTimer);
    clearTimeout(chunkTimer);
    clearTimeout(indexTimer);

    if (!res.ok) {
      const err = await res.json();
      onStepChange?.("error");
      return { success: false, message: err.detail || "Upload failed." };
    }

    const data = await res.json();
    onStepChange?.("completed");
    return {
      success: true,
      message: data.message,
      document: data.document,
    };
  } catch (err: any) {
    onStepChange?.("error");
    return {
      success: false,
      message: err.message || "Network error uploading PDF.",
    };
  }
}

export async function deleteDocument(id: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/documents/${id}`, {
      method: "DELETE",
    });
    return res.ok;
  } catch (err) {
    console.error("deleteDocument error:", err);
    return false;
  }
}

export async function fetchAnalyticsStats(): Promise<AnalyticsStats | null> {
  try {
    const res = await fetch(`${API_BASE}/api/analytics/stats`);
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    console.error("fetchAnalyticsStats error:", err);
    return null;
  }
}
