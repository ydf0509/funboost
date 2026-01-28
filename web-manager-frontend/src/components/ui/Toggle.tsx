import clsx from "clsx";

type ToggleProps = {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  size?: "sm" | "md";
  disabled?: boolean;
};

export function Toggle({ checked, onChange, label, size = "md", disabled = false }: ToggleProps) {
  const sizeClasses = {
    sm: {
      track: "w-8 h-4",
      thumb: "h-3 w-3",
      translate: "translate-x-4",
    },
    md: {
      track: "w-11 h-6",
      thumb: "h-5 w-5",
      translate: "translate-x-5",
    },
  };

  const s = sizeClasses[size];

  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => !disabled && onChange(!checked)}
      className={clsx(
        "group relative inline-flex items-center gap-2",
        disabled && "opacity-50 cursor-not-allowed"
      )}
    >
      {/* Switch Track */}
      <span
        className={clsx(
          "relative inline-flex flex-shrink-0 rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none",
          s.track,
          checked
            ? "bg-[hsl(var(--accent))]"
            : "bg-[hsl(var(--sand-2))]",
          !disabled && "cursor-pointer"
        )}
      >
        {/* Switch Thumb */}
        <span
          className={clsx(
            "pointer-events-none inline-block rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out",
            s.thumb,
            checked ? s.translate : "translate-x-0"
          )}
        />
      </span>

      {/* Label */}
      {label && (
        <span className="text-sm text-[hsl(var(--ink))]">
          {label}
        </span>
      )}
    </button>
  );
}
