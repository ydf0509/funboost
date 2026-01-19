"use client";

import { useEffect, useCallback } from "react";
import { X } from "lucide-react";
import clsx from "clsx";
import { Button } from "./Button";

const sizes = {
  sm: "max-w-md",
  md: "max-w-xl",
  lg: "max-w-3xl",
  xl: "max-w-5xl",
};

type ModalProps = {
  open: boolean;
  title: string;
  onClose: () => void;
  children: React.ReactNode;
  footer?: React.ReactNode;
  size?: keyof typeof sizes;
  /** Optional subtitle for additional context */
  subtitle?: string;
};

export function Modal({ open, title, onClose, children, footer, size = "lg", subtitle }: ModalProps) {
  // Handle ESC key to close modal
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === "Escape") onClose();
  }, [onClose]);

  useEffect(() => {
    if (!open) return;
    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.body.style.overflow = "";
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open, handleKeyDown]);

  if (!open) return null;

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center px-4 py-10"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      {/* Backdrop with glassmorphism effect */}
      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-md transition-opacity duration-300 ease-out" 
        onClick={onClose}
        aria-hidden="true"
      />
      
      {/* Modal container with enhanced styling */}
      <div 
        className={clsx(
          "relative w-full rounded-3xl p-8 shadow-2xl",
          "bg-[hsl(var(--card))]/95 backdrop-blur-xl",
          "border border-[hsl(var(--line))]/50",
          "animate-in fade-in-0 zoom-in-95 duration-300 ease-out",
          sizes[size]
        )}
      >
        {/* Header with improved visual hierarchy */}
        <div className="flex items-start justify-between border-b border-[hsl(var(--line))]/60 pb-4 mb-2">
          <div className="flex-1 pr-4">
            <h2 
              id="modal-title"
              className="font-display text-xl font-semibold text-[hsl(var(--ink))] tracking-tight"
            >
              {title}
            </h2>
            {subtitle && (
              <p className="mt-1 text-sm text-[hsl(var(--ink-muted))]">{subtitle}</p>
            )}
          </div>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={onClose}
            className="cursor-pointer -mr-2 -mt-1 hover:bg-[hsl(var(--sand-2))] rounded-xl transition-colors duration-200"
            aria-label="关闭弹窗"
          >
            <X className="h-5 w-5" />
          </Button>
        </div>
        
        {/* Content area with custom scrollbar */}
        <div 
          className={clsx(
            "max-h-[65vh] overflow-y-auto py-4 text-sm text-[hsl(var(--ink))]",
            "scrollbar-thin scrollbar-thumb-[hsl(var(--line))] scrollbar-track-transparent",
            "pr-2 -mr-2" // Offset for scrollbar
          )}
        >
          {children}
        </div>
        
        {/* Footer with improved spacing */}
        {footer && (
          <div className="border-t border-[hsl(var(--line))]/60 pt-5 mt-2">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}
