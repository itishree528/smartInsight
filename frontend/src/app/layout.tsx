import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SmartInsight – AI-Powered Document Search & Analytics Engine",
  description:
    "FastAPI, Next.js, pgvector, and Redis document intelligence engine with SSE streaming and semantic caching.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased min-h-screen bg-slate-950 text-slate-100 flex flex-col">
        {children}
      </body>
    </html>
  );
}
