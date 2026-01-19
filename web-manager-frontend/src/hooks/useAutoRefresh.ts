import { useCallback, useState } from "react";
import { useInterval } from "./useInterval";

export function useAutoRefresh(callback: () => void, initialEnabled = false, intervalMs = 10000) {
  const [enabled, setEnabled] = useState(initialEnabled);

  const toggle = useCallback(() => setEnabled((prev) => !prev), []);

  useInterval(() => {
    if (enabled) {
      callback();
    }
  }, enabled ? intervalMs : null);

  return { enabled, toggle, setEnabled };
}
