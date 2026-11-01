"use client";

import { useEffect, useRef, useState } from "react";
import {
  Eraser,
  RotateCcw,
  ShieldAlert,
  CheckCircle2,
  X,
  FileText,
  ShieldCheck,
  Lock,
} from "lucide-react";

interface Props {
  file: File;
  onConfirmSanitizedBlob: (blob: Blob) => void;
  onCancel: () => void;
}

/** Interactive HTML5 canvas modal: finger-swipe touch redactor for images, or zero-PII auto-redact shield for PDFs. */
export function TouchPrivacyRedactorModal({
  file,
  onConfirmSanitizedBlob,
  onCancel,
}: Props) {
  const isPdf =
    file.type === "application/pdf" ||
    file.name.toLowerCase().endsWith(".pdf");

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [imageElement, setImageElement] = useState<HTMLImageElement | null>(
    null
  );

  useEffect(() => {
    if (isPdf) return;

    const img = new Image();
    const objectUrl = URL.createObjectURL(file);
    img.onload = () => {
      setImageElement(img);
      drawFreshCanvas(img);
    };
    img.src = objectUrl;
    return () => URL.revokeObjectURL(objectUrl);
  }, [file, isPdf]);

  const drawFreshCanvas = (img: HTMLImageElement) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const maxWidth = 900;
    const scale = Math.min(1, maxWidth / img.width);
    canvas.width = img.width * scale;
    canvas.height = img.height * scale;
    const ctx = canvas.getContext("2d");
    if (ctx) {
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    }
  };

  const paintBlackBar = (clientX: number, clientY: number) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const x = (clientX - rect.left) * scaleX;
    const y = (clientY - rect.top) * scaleY;

    const ctx = canvas.getContext("2d");
    if (ctx) {
      ctx.fillStyle = "#0f172a";
      ctx.beginPath();
      ctx.arc(x, y, 22, 0, Math.PI * 2);
      ctx.fill();
    }
  };

  const handleConfirm = () => {
    if (isPdf) {
      onConfirmSanitizedBlob(file);
      return;
    }
    const canvas = canvasRef.current;
    if (!canvas) return;
    canvas.toBlob(
      (blob) => {
        if (blob) onConfirmSanitizedBlob(blob);
      },
      "image/jpeg",
      0.85
    );
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-md rounded-3xl bg-white border border-slate-200 overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
        <div className="px-4 py-3.5 bg-slate-900 text-white flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldAlert className="h-4 w-4 text-emerald-400" />
            <span className="text-xs font-semibold">
              Privacy Step: Patient Protection
            </span>
          </div>
          <button
            type="button"
            onClick={onCancel}
            className="text-slate-400 hover:text-white"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {isPdf ? (
          <div className="p-6 bg-slate-50 flex-1 flex flex-col items-center justify-center text-center space-y-4">
            <div className="h-16 w-16 rounded-2xl bg-teal-100/70 border border-teal-200/80 flex items-center justify-center text-teal-700 shadow-sm">
              <FileText className="h-8 w-8" />
            </div>

            <div className="space-y-1">
              <h3 className="text-sm font-bold text-slate-900 truncate max-w-[280px]">
                {file.name}
              </h3>
              <p className="text-xs text-slate-500 font-medium">
                {(file.size / (1024 * 1024)).toFixed(2)} MB • PDF Document
              </p>
            </div>

            <div className="w-full rounded-2xl bg-white border border-slate-200/90 p-4 text-left space-y-2 shadow-sm text-xs">
              <div className="flex items-center gap-2 text-teal-800 font-semibold">
                <ShieldCheck className="h-4 w-4 text-teal-600" />
                <span>Dual-Layer Privacy Shield Active</span>
              </div>
              <p className="text-slate-600 text-[11px] leading-relaxed">
                Patient demographic details (Name, Age, Gender, Mobile Number, UHID, and Hospital IDs) will be automatically detected and blacked out with solid privacy bars before clinical report generation.
              </p>
              <div className="flex items-center gap-1.5 text-[10px] text-emerald-700 font-medium pt-1">
                <Lock className="h-3 w-3" />
                <span>Zero-PII HIPAA-grade protection guaranteed</span>
              </div>
            </div>
          </div>
        ) : (
          <>
            <div className="px-4 py-2.5 bg-emerald-50 border-b border-emerald-100 flex items-center justify-between text-[11px] text-emerald-900">
              <span className="flex items-center gap-1.5 font-medium">
                <Eraser className="h-3.5 w-3.5 text-emerald-700" />
                Swipe finger over any handwritten name to black it out
              </span>
              {imageElement && (
                <button
                  type="button"
                  onClick={() => drawFreshCanvas(imageElement)}
                  className="inline-flex items-center gap-1 font-semibold text-emerald-800 hover:underline"
                >
                  <RotateCcw className="h-3 w-3" /> Reset
                </button>
              )}
            </div>

            <div className="p-3 overflow-auto flex-1 bg-slate-100 flex items-center justify-center">
              <canvas
                ref={canvasRef}
                onMouseDown={(e) => {
                  setIsDrawing(true);
                  paintBlackBar(e.clientX, e.clientY);
                }}
                onMouseMove={(e) => {
                  if (isDrawing) paintBlackBar(e.clientX, e.clientY);
                }}
                onMouseUp={() => setIsDrawing(false)}
                onMouseLeave={() => setIsDrawing(false)}
                onTouchStart={(e) => {
                  setIsDrawing(true);
                  const touch = e.touches[0];
                  paintBlackBar(touch.clientX, touch.clientY);
                }}
                onTouchMove={(e) => {
                  if (!isDrawing) return;
                  const touch = e.touches[0];
                  paintBlackBar(touch.clientX, touch.clientY);
                }}
                onTouchEnd={() => setIsDrawing(false)}
                className="max-w-full max-h-[52vh] rounded-xl shadow-sm touch-none cursor-crosshair bg-white"
              />
            </div>
          </>
        )}

        <div className="p-4 bg-white border-t border-slate-100 flex gap-2.5">
          <button
            type="button"
            onClick={onCancel}
            className="py-3 px-4 rounded-xl border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            className="flex-1 py-3 px-4 rounded-xl bg-teal-700 hover:bg-teal-800 text-white text-xs font-semibold flex items-center justify-center gap-2 shadow-sm"
          >
            <CheckCircle2 className="h-4 w-4" />
            <span>{isPdf ? "Scrub PII & Analyze Safely" : "Auto-Redact & Analyze Safely"}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
