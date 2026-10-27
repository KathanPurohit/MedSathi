"use client";

import { useState } from "react";
import { Eye, EyeOff, ShieldCheck } from "lucide-react";

interface Props {
  redactedImageDataUrl: string;
}

/** Collapsible trust badge allowing users to verify the exact PII-blacked-out image sent to the AI. */
export function RedactedProofPreview({ redactedImageDataUrl }: Props) {
  const [isOpen, setIsOpen] = useState(false);

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
            </>
          )}
        </button>
      </div>

      {isOpen && (
        <div className="mt-3 pt-3 border-t border-emerald-800/70">
          <img
            src={redactedImageDataUrl}
            alt="Redacted prescription proof"
            className="w-full rounded-xl border border-emerald-800 max-h-64 object-contain bg-black"
          />
        </div>
      )}
    </div>
  );
}
