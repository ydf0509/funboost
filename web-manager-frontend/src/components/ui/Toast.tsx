"use client";

import { useEffect, useState } from "react";
import { CheckCircle, XCircle, AlertCircle, X } from "lucide-react";

export type ToastType = "success" | "error" | "warning" | "info";

type ToastProps = {
  message: string;
  type?: ToastType;
  duration?: number;
  onClose: () => void;
};

export function Toast({ message, type = "info", duration = 3000, onClose }: ToastProps) {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false);
      setTimeout(onClose, 300);
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onClose]);

  const icons = {
    success: <CheckCircle className="h-5 w-5 text-[hsl(var(--success))]" />,
    error: <XCircle className="h-5 w-5 text-[hsl(var(--danger))]" />,
    warning: <AlertCircle className="h-5 w-5 text-[hsl(var(--warning))]" />,
    info: <AlertCircle className="h-5 w-5 text-[hsl(var(--accent))]" />,
  };

  const bgColors = {
    success: "border-[hsl(var(--success))]/30 bg-[hsl(var(--success))]/10",
    error: "border-[hsl(var(--danger))]/30 bg-[hsl(var(--danger))]/10",
    warning: "border-[hsl(var(--warning))]/30 bg-[hsl(var(--warning))]/10",
    info: "border-[hsl(var(--accent))]/30 bg-[hsl(var(--accent))]/10",
  };

  return (
    <div
      className={`flex items-center gap-3 rounded-xl border px-4 py-3 shadow-lg backdrop-blur-sm transition-all duration-300 ${bgColors[type]} ${
        visible ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0"
      }`}
    >
      {icons[type]}
      <span className="text-sm text-[hsl(var(--ink))]">{message}</span>
      <button
        onClick={() => {
          setVisible(false);
          setTimeout(onClose, 300);
        }}
        className="ml-2 p-1 rounded-full hover:bg-[hsl(var(--sand-2))] text-[hsl(var(--ink-muted))] hover:text-[hsl(var(--ink))]"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}

// Toast 容器，用于管理多个 toast
type ToastItem = {
  id: number;
  message: string;
  type: ToastType;
};

type ToastContainerProps = {
  toasts: ToastItem[];
  onRemove: (id: number) => void;
};

export function ToastContainer({ toasts, onRemove }: ToastContainerProps) {
  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col-reverse gap-2">
      {toasts.map((toast) => (
        <Toast
          key={toast.id}
          message={toast.message}
          type={toast.type}
          onClose={() => onRemove(toast.id)}
        />
      ))}
    </div>
  );
}
