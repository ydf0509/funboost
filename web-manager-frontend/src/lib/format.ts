export function formatNumber(value: number) {
  return new Intl.NumberFormat("zh-CN").format(value);
}

export function formatDateTime(value?: string | number | null) {
  if (!value) return "-";
  const date = typeof value === "number" ? new Date(value * 1000) : new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export function formatDuration(seconds?: number | null) {
  if (seconds === undefined || seconds === null) return "-";
  if (seconds < 1) return `${Math.round(seconds * 1000)} 毫秒`;
  if (seconds < 60) return `${seconds.toFixed(2)} 秒`;
  const mins = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  return `${mins} 分 ${remainder.toFixed(1)} 秒`;
}

export function toDateInputValue(date: Date) {
  const pad = (num: number) => String(num).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

export function toDateTimeInputValue(date: Date) {
  const pad = (num: number) => String(num).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(
    date.getHours()
  )}:${pad(date.getMinutes())}`;
}

export function toBackendDateTime(value: string) {
  if (!value) return "";
  const normalized = value.includes("T") ? value.replace("T", " ") : value;
  return normalized.length === 16 ? `${normalized}:00` : normalized;
}
