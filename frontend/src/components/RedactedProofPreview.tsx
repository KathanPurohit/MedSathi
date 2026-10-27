"use client";

import { useState } from "react";
import { Eye, EyeOff, ShieldCheck, ChevronLeft, ChevronRight, FileText } from "lucide-react";

interface Props {
  redactedImageDataUrl: string;
  redactedPages?: string[];
}

/** Collapsible trust badge allowing users to inspect the exact PII-blacked-out images across all pages. */
export function RedactedProofPreview({
  redactedImageDataUrl,
  redactedPages,
}: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [currentPageIndex, setCurrentPageIndex] = useState(0);

  const pages = redactedPages && redactedPages.length > 0 ? redactedPages : [redactedImageDataUrl];
  const totalPages = pages.length;
  const currentSrc = pages[currentPageIndex] || redactedImageDataUrl;

  return (
    <div className="rounded-2xl bg-emerald-950 text-emerald-50 px-4 py-3 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-emerald-400 shrink-0" />
          <span className="text-xs font-medium">
            Privacy Verified: Personal details scrubbed before AI scan
          </span>
        </div>
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="text-[11px] font-semibold text-emerald-300 hover:text-white flex items-center gap-1 shrink-0 ml-2"
        >
          {isOpen ? (
            <>
              <EyeOff className="h-3.5 w-3.5" /> Hide Proof
            </>
          ) : (
            <>
              <Eye className="h-3.5 w-3.5" /> View Proof
              {totalPages > 1 && (
                <span className="ml-1 px-1.5 py-0.2 rounded-full bg-emerald-800 text-[10px]">
                  {totalPages}p
                </span>
              )}
            </>
          )}
        </button>
      </div>

      {isOpen && (
        <div className="mt-3 pt-3 border-t border-emerald-800/70 space-y-2.5">
          {totalPages > 1 && (
            <div className="flex items-center justify-between text-xs text-emerald-200 px-1">
              <span className="flex items-center gap-1 font-medium">
                <FileText className="h-3.5 w-3.5 text-emerald-400" />
                Page {currentPageIndex + 1} of {totalPages}
              </span>
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  disabled={currentPageIndex === 0}
                  onClick={() => setCurrentPageIndex((p) => Math.max(0, p - 1))}
                  className="p-1 rounded-lg bg-emerald-900/80 hover:bg-emerald-800 disabled:opacity-40 transition-all"
                  aria-label="Previous Page"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  disabled={currentPageIndex === totalPages - 1}
                  onClick={() =>
                    setCurrentPageIndex((p) => Math.min(totalPages - 1, p + 1))
                  }
                  className="p-1 rounded-lg bg-emerald-900/80 hover:bg-emerald-800 disabled:opacity-40 transition-all"
                  aria-label="Next Page"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}

          <img
            key={currentPageIndex}
            src={currentSrc}
            alt={`Redacted medical proof page ${currentPageIndex + 1}`}
            className="w-full rounded-xl border border-emerald-800 max-h-72 object-contain bg-black transition-all"
          />

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-1.5 pt-1">
              {pages.map((_, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setCurrentPageIndex(idx)}
                  className={`h-1.5 rounded-full transition-all ${
                    idx === currentPageIndex
                      ? "w-5 bg-emerald-400"
                      : "w-1.5 bg-emerald-800 hover:bg-emerald-600"
                  }`}
                  aria-label={`Go to page ${idx + 1}`}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
