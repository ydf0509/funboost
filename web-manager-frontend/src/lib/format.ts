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

function pad2(num: number) {
  return String(num).padStart(2, "0");
}

function formatDateToSeconds(date: Date) {
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())} ${pad2(date.getHours())}:${pad2(
    date.getMinutes()
  )}:${pad2(date.getSeconds())}`;
}

function parseToLocalDate(value: string): Date | null {
  const raw = value.trim();
  if (!raw) return null;

  // Normalize common zh-CN formats and separators.
  const normalized = raw
    .replace(/\//g, "-")
    .replace(/年/g, "-")
    .replace(/月/g, "-")
    .replace(/日/g, "")
    .replace(/\s+/g, " ")
    .trim();

  // YYYY-MM-DD HH:mm(:ss)?
  const m = normalized.match(
    /^(\d{4})-(\d{1,2})-(\d{1,2})(?:[ T])(\d{1,2}):(\d{2})(?::(\d{2}))?$/
  );
  if (m) {
    const year = Number(m[1]);
    const month = Number(m[2]);
    const day = Number(m[3]);
    const hour = Number(m[4]);
    const minute = Number(m[5]);
    const second = Number(m[6] ?? 0);
    const date = new Date(year, month - 1, day, hour, minute, second);
    return Number.isNaN(date.getTime()) ? null : date;
  }

  // Fall back to native parsing for ISO-like strings.
  const iso = normalized.includes("T") ? normalized : normalized.replace(" ", "T");
  const parsed = new Date(iso);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

/**
 * Format datetime with second precision: YYYY-MM-DD HH:mm:ss
 * - number: treated as unix timestamp (seconds; ms auto-detected)
 * - string: best-effort parse common backend/zh-CN formats
 */
export function formatDateTimeSeconds(value?: string | number | null) {
  if (value === undefined || value === null) return "-";
  if (typeof value === "number") {
    const ms = value > 1e12 ? value : value * 1000;
    const date = new Date(ms);
    if (Number.isNaN(date.getTime())) return "-";
    return formatDateToSeconds(date);
  }
  if (value === "") return "-";
  const parsed = parseToLocalDate(value);
  if (!parsed) {
    const fallback = value.trim();
    return fallback ? fallback : "-";
  }
  return formatDateToSeconds(parsed);
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
