"use client";

import { useEffect, useRef, useState } from "react";
import { Eraser, RotateCcw, ShieldAlert, CheckCircle2, X } from "lucide-react";

interface Props {
  file: File;
  onConfirmSanitizedBlob: (blob: Blob) => void;
  onCancel: () => void;
}

/** Interactive HTML5 canvas modal allowing the user to finger-swipe black bars over any handwritten names before upload. */
export function TouchPrivacyRedactorModal({
  file,
  onConfirmSanitizedBlob,
  onCancel,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [imageElement, setImageElement] = useState<HTMLImageElement | null>(
    null
  );

  useEffect(() => {
    const img = new Image();
    const objectUrl = URL.createObjectURL(file);
    img.onload = () => {
      setImageElement(img);
      drawFreshCanvas(img);
    };
    img.src = objectUrl;
    return () => URL.revokeObjectURL(objectUrl);
  }, [file]);

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
    const canvas = canvasRef.current;
    if (!canvas) return;
    canvas.toBlob(
      (blob) => {
        if (blob) onConfirmSanitizedBlob(blob);
      },
      "image/jpeg",
      0.92
    );
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-md rounded-3xl bg-white border border-slate-200 overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
        <div className="px-4 py-3.5 bg-slate-900 text-white flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldAlert className="h-4 w-4 text-emerald-400" />
            <span className="text-xs font-semibold">
              Privacy Step: Hide Patient Name (Optional)
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
            <span>Auto-Redact & Analyze Safely</span>
          </button>
        </div>
      </div>
    </div>
  );
}
